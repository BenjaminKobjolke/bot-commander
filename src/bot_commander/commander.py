"""Generic command routing and conversation management."""

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from .config.constants import (
    ERR_COMMAND_DISABLED,
    ERR_CONVERSATION_EXPIRED,
    ERR_OPERATION_CANCELLED,
    ERR_UNKNOWN_COMMAND,
)
from .conversation import ConversationState, is_confirmed_sentinel
from .types import BotMessage, BotResponse

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

CommandHandler = Callable[[str, str], BotResponse]
"""Handler for a registered command. Receives (user_id, args) and returns BotResponse."""

ConversationHandler = Callable[
    [ConversationState, str], tuple[ConversationState | None, BotResponse]
]
"""Handler for a conversation step.

Receives (state, text) and returns (new_state | None, response).
"""


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class MessageHandler(Protocol):
    """Protocol for objects that handle incoming bot messages."""

    def handle(self, message: BotMessage) -> BotResponse: ...


# ---------------------------------------------------------------------------
# Internal DTOs
# ---------------------------------------------------------------------------


class _CommandRegistration:
    """Internal record for a registered command."""

    __slots__ = ("handler", "requires_permission")

    def __init__(
        self,
        handler: CommandHandler,
        requires_permission: str | None,
    ) -> None:
        self.handler = handler
        self.requires_permission = requires_permission


class _ConversationRegistration:
    """Internal record for a registered conversation kind."""

    __slots__ = ("handler", "on_confirmed")

    def __init__(
        self,
        handler: ConversationHandler,
        on_confirmed: Callable[[dict], BotResponse] | None,
    ) -> None:
        self.handler = handler
        self.on_confirmed = on_confirmed


# ---------------------------------------------------------------------------
# Commander
# ---------------------------------------------------------------------------


class Commander:
    """Generic command router and conversation manager.

    Projects compose with or subclass ``Commander``, calling
    :meth:`register_command` and :meth:`register_conversation` to set up their
    specific commands.  The :meth:`handle` method implements the
    :class:`MessageHandler` protocol.
    """

    def __init__(
        self,
        *,
        unknown_command_text: str = ERR_UNKNOWN_COMMAND,
        command_disabled_text: str = ERR_COMMAND_DISABLED,
        expired_text: str = ERR_CONVERSATION_EXPIRED,
        cancelled_text: str = ERR_OPERATION_CANCELLED,
        cancel_command: str = "/cancel",
    ) -> None:
        self._unknown_command_text = unknown_command_text
        self._command_disabled_text = command_disabled_text
        self._expired_text = expired_text
        self._cancelled_text = cancelled_text
        self._cancel_command = cancel_command.lower()

        self._command_registry: dict[str, _CommandRegistration] = {}
        self._conversation_registry: dict[str, _ConversationRegistration] = {}
        self._conversations: dict[str, ConversationState] = {}
        self._permission_checker: Callable[[str, str], bool] | None = None

    # ------------------------------------------------------------------
    # Registration API
    # ------------------------------------------------------------------

    def register_command(
        self,
        name: str,
        handler: CommandHandler,
        *,
        requires_permission: str | None = None,
    ) -> None:
        """Register a command handler.

        Parameters
        ----------
        name:
            The command string (e.g. ``"/list"``).  Stored lower-cased.
        handler:
            Callable receiving ``(user_id, args)`` and returning
            :class:`BotResponse`.
        requires_permission:
            Optional permission string.  If set, the registered permission
            checker must return ``True`` for this string before the handler
            is invoked.
        """
        self._command_registry[name.lower()] = _CommandRegistration(
            handler=handler,
            requires_permission=requires_permission,
        )

    def register_conversation(
        self,
        kind: str,
        handler: ConversationHandler,
        on_confirmed: Callable[[dict], BotResponse] | None = None,
    ) -> None:
        """Register a conversation kind with an optional confirmation callback.

        Parameters
        ----------
        kind:
            Identifier for this conversation type (e.g. ``"add_wizard"``).
        handler:
            Callable receiving ``(state, text)`` and returning
            ``(new_state | None, response)``.  Returning ``None`` as the
            new state signals that the conversation is finished.
        on_confirmed:
            Optional callback invoked when the handler finishes *and* the
            response text equals the confirmed sentinel.  Receives the
            conversation ``state.data`` dict.  **Important:** handlers must
            mutate ``state.data`` in place (not replace the dict) for
            accumulated data to be visible to ``on_confirmed``.
        """
        self._conversation_registry[kind] = _ConversationRegistration(
            handler=handler,
            on_confirmed=on_confirmed,
        )

    def set_permission_checker(self, checker: Callable[[str, str], bool]) -> None:
        """Set the permission check function.

        Parameters
        ----------
        checker:
            Callable receiving ``(permission_name, user_id)`` and returning
            ``True`` if the action is allowed for that user.
        """
        self._permission_checker = checker

    # ------------------------------------------------------------------
    # Conversation management
    # ------------------------------------------------------------------

    def start_conversation(self, user_id: str, state: ConversationState) -> None:
        """Start (or replace) a conversation for *user_id*."""
        self._conversations[user_id] = state

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def handle(self, message: BotMessage) -> BotResponse:
        """Route an incoming message to the appropriate handler.

        Implements the :class:`MessageHandler` protocol.

        Behaviour:
        1. Clean up expired conversations (return expired text if one was removed).
        2. If the user has an active conversation, continue it (or cancel).
        3. Otherwise parse the command and dispatch to a registered handler.
        """
        user_id = message.user_id

        # 1. Expired conversation cleanup
        if self._cleanup_expired(user_id):
            return BotResponse(text=self._expired_text)

        # 2. Active conversation
        if user_id in self._conversations:
            if message.text.strip().lower() == self._cancel_command:
                return self._cancel_conversation(user_id)
            return self._continue_conversation(user_id, message.text)

        # 3. Command routing
        parts = message.text.strip().split(maxsplit=1)
        command = parts[0].lower() if parts else ""
        args = parts[1].strip() if len(parts) > 1 else ""

        if not command:
            return BotResponse(text=self._unknown_command_text)

        registration = self._command_registry.get(command)
        if registration is None:
            return BotResponse(text=self._unknown_command_text)

        # Permission check
        if (
            registration.requires_permission is not None
            and self._permission_checker is not None
            and not self._permission_checker(registration.requires_permission, user_id)
        ):
            return BotResponse(text=self._command_disabled_text.format(command))

        return registration.handler(user_id, args)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cleanup_expired(self, user_id: str) -> bool:
        """Remove an expired conversation for *user_id*. Return True if one was removed."""
        if user_id in self._conversations and self._conversations[user_id].is_expired():
            del self._conversations[user_id]
            return True
        return False

    def _cancel_conversation(self, user_id: str) -> BotResponse:
        """Cancel the active conversation for *user_id*."""
        del self._conversations[user_id]
        return BotResponse(text=self._cancelled_text)

    def _continue_conversation(self, user_id: str, text: str) -> BotResponse:
        """Advance the active conversation for *user_id*."""
        state = self._conversations[user_id]
        conv_reg = self._conversation_registry.get(state.kind)
        if conv_reg is None:
            del self._conversations[user_id]
            return BotResponse(text=self._unknown_command_text)

        new_state, response = conv_reg.handler(state, text)
        if new_state is None:
            del self._conversations[user_id]
            if is_confirmed_sentinel(response.text) and conv_reg.on_confirmed:
                return conv_reg.on_confirmed(state.data)
            return response
        self._conversations[user_id] = new_state
        return response
