"""Tests for bot_commander.commander."""

import time
from typing import Protocol

from bot_commander.commander import (
    Commander,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
)
from bot_commander.config.constants import (
    CONFIRMED_SENTINEL,
    ERR_COMMAND_DISABLED,
    ERR_CONVERSATION_EXPIRED,
    ERR_OPERATION_CANCELLED,
    ERR_UNKNOWN_COMMAND,
)
from bot_commander.conversation import ConversationState, confirmed_response
from bot_commander.types import BotMessage, BotResponse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _echo_handler(user_id: str, args: str) -> BotResponse:
    """Simple command handler that echoes back user_id and args."""
    return BotResponse(text=f"echo:{user_id}:{args}")


def _greet_handler(user_id: str, args: str) -> BotResponse:
    """Command handler returning a greeting."""
    return BotResponse(text=f"Hello, {user_id}!")


def _simple_conversation_handler(
    state: ConversationState, text: str
) -> tuple[ConversationState | None, BotResponse]:
    """Conversation handler: step 0 asks for name, step 1 finishes."""
    if state.step == 0:
        new_state = ConversationState(
            kind=state.kind, step=1, data={"name": text}, expires_at=state.expires_at
        )
        return new_state, BotResponse(text="Got name. Send confirmation.")
    # Step 1: confirm
    if text.lower() == "yes":
        state.data["confirmed"] = True
        return None, confirmed_response()
    return None, BotResponse(text="Cancelled by user.")


def _single_step_conversation_handler(
    state: ConversationState, text: str
) -> tuple[ConversationState | None, BotResponse]:
    """Conversation handler that finishes immediately without confirmation."""
    return None, BotResponse(text=f"done:{text}")


# ---------------------------------------------------------------------------
# MessageHandler Protocol tests
# ---------------------------------------------------------------------------


class TestMessageHandlerProtocol:
    """Tests for the MessageHandler protocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        assert hasattr(MessageHandler, "__protocol_attrs__") or issubclass(
            type(MessageHandler), type(Protocol)
        )

    def test_commander_implements_message_handler(self) -> None:
        commander = Commander()
        assert isinstance(commander, MessageHandler)

    def test_custom_class_implements_protocol(self) -> None:
        class MyHandler:
            def handle(self, message: BotMessage) -> BotResponse:
                return BotResponse(text="ok")

        handler = MyHandler()
        assert isinstance(handler, MessageHandler)

    def test_non_handler_does_not_match(self) -> None:
        class NotAHandler:
            def process(self, message: BotMessage) -> BotResponse:
                return BotResponse(text="ok")

        assert not isinstance(NotAHandler(), MessageHandler)


# ---------------------------------------------------------------------------
# Type alias tests
# ---------------------------------------------------------------------------


class TestTypeAliases:
    """Tests for CommandHandler and ConversationHandler type aliases."""

    def test_command_handler_callable(self) -> None:
        """CommandHandler should accept (str, str) -> BotResponse callables."""
        handler: CommandHandler = _echo_handler
        result = handler("user1", "arg1")
        assert isinstance(result, BotResponse)
        assert result.text == "echo:user1:arg1"

    def test_conversation_handler_callable(self) -> None:
        """ConversationHandler should accept the correct signature."""
        handler: ConversationHandler = _simple_conversation_handler
        state = ConversationState(kind="test")
        new_state, response = handler(state, "Alice")
        assert new_state is not None
        assert isinstance(response, BotResponse)


# ---------------------------------------------------------------------------
# Commander: Command Registration & Routing
# ---------------------------------------------------------------------------


class TestCommandRegistrationAndRouting:
    """Tests for registering commands and routing messages."""

    def test_register_and_handle_command(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)

        response = cmd.handle(BotMessage(user_id="u1", text="/echo hello world"))
        assert response.text == "echo:u1:hello world"

    def test_register_multiple_commands(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)
        cmd.register_command("/greet", _greet_handler)

        r1 = cmd.handle(BotMessage(user_id="u1", text="/echo test"))
        r2 = cmd.handle(BotMessage(user_id="u1", text="/greet"))
        assert r1.text == "echo:u1:test"
        assert r2.text == "Hello, u1!"

    def test_unknown_command_returns_default_text(self) -> None:
        cmd = Commander()
        response = cmd.handle(BotMessage(user_id="u1", text="/unknown"))
        assert response.text == ERR_UNKNOWN_COMMAND

    def test_unknown_command_custom_text(self) -> None:
        cmd = Commander(unknown_command_text="No such command.")
        response = cmd.handle(BotMessage(user_id="u1", text="/nope"))
        assert response.text == "No such command."

    def test_command_with_no_args(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)

        response = cmd.handle(BotMessage(user_id="u1", text="/echo"))
        assert response.text == "echo:u1:"

    def test_command_parsing_case_insensitive(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)

        response = cmd.handle(BotMessage(user_id="u1", text="/ECHO hello"))
        assert response.text == "echo:u1:hello"

    def test_command_with_leading_whitespace(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)

        response = cmd.handle(BotMessage(user_id="u1", text="  /echo hi"))
        assert response.text == "echo:u1:hi"

    def test_empty_message_returns_unknown(self) -> None:
        cmd = Commander()
        response = cmd.handle(BotMessage(user_id="u1", text=""))
        assert response.text == ERR_UNKNOWN_COMMAND

    def test_whitespace_only_message_returns_unknown(self) -> None:
        cmd = Commander()
        response = cmd.handle(BotMessage(user_id="u1", text="   "))
        assert response.text == ERR_UNKNOWN_COMMAND


# ---------------------------------------------------------------------------
# Commander: Permission Checking
# ---------------------------------------------------------------------------


class TestPermissionChecking:
    """Tests for permission checking with registered commands."""

    def test_command_with_permission_allowed(self) -> None:
        cmd = Commander()
        cmd.register_command("/admin", _echo_handler, requires_permission="admin")
        cmd.set_permission_checker(lambda perm, uid: perm == "admin")

        response = cmd.handle(BotMessage(user_id="u1", text="/admin do stuff"))
        assert response.text == "echo:u1:do stuff"

    def test_command_with_permission_denied(self) -> None:
        cmd = Commander()
        cmd.register_command("/admin", _echo_handler, requires_permission="admin")
        cmd.set_permission_checker(lambda perm, uid: False)

        response = cmd.handle(BotMessage(user_id="u1", text="/admin do stuff"))
        assert response.text == ERR_COMMAND_DISABLED.format("/admin")

    def test_command_disabled_custom_text(self) -> None:
        cmd = Commander(command_disabled_text="Nope: {}")
        cmd.register_command("/admin", _echo_handler, requires_permission="admin")
        cmd.set_permission_checker(lambda perm, uid: False)

        response = cmd.handle(BotMessage(user_id="u1", text="/admin"))
        assert response.text == "Nope: /admin"

    def test_command_without_permission_requirement_always_allowed(self) -> None:
        cmd = Commander()
        cmd.register_command("/public", _echo_handler)
        cmd.set_permission_checker(lambda perm, uid: False)

        response = cmd.handle(BotMessage(user_id="u1", text="/public hi"))
        assert response.text == "echo:u1:hi"

    def test_permission_checker_receives_user_id(self) -> None:
        """Permission checker should receive both permission name and user_id."""
        received: list[tuple[str, str]] = []

        def checker(perm: str, uid: str) -> bool:
            received.append((perm, uid))
            return True

        cmd = Commander()
        cmd.register_command("/admin", _echo_handler, requires_permission="admin")
        cmd.set_permission_checker(checker)

        cmd.handle(BotMessage(user_id="user42", text="/admin test"))
        assert received == [("admin", "user42")]

    def test_per_user_permission(self) -> None:
        """Permission checker can allow/deny per user."""
        cmd = Commander()
        cmd.register_command("/admin", _echo_handler, requires_permission="admin")
        cmd.set_permission_checker(lambda perm, uid: uid == "admin_user")

        r1 = cmd.handle(BotMessage(user_id="admin_user", text="/admin go"))
        r2 = cmd.handle(BotMessage(user_id="regular_user", text="/admin go"))
        assert r1.text == "echo:admin_user:go"
        assert r2.text == ERR_COMMAND_DISABLED.format("/admin")

    def test_no_permission_checker_set_allows_all(self) -> None:
        """When no permission checker is set, all commands should be allowed."""
        cmd = Commander()
        cmd.register_command("/admin", _echo_handler, requires_permission="admin")

        response = cmd.handle(BotMessage(user_id="u1", text="/admin test"))
        assert response.text == "echo:u1:test"


# ---------------------------------------------------------------------------
# Commander: Conversation Management
# ---------------------------------------------------------------------------


class TestConversationManagement:
    """Tests for starting and continuing conversations."""

    def test_start_and_continue_conversation(self) -> None:
        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        # Step 0: provide name
        r1 = cmd.handle(BotMessage(user_id="u1", text="Alice"))
        assert r1.text == "Got name. Send confirmation."

        # Step 1: confirm
        r2 = cmd.handle(BotMessage(user_id="u1", text="no"))
        assert r2.text == "Cancelled by user."

    def test_conversation_takes_priority_over_commands(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        # Even though /echo is registered, active conversation takes priority
        response = cmd.handle(BotMessage(user_id="u1", text="/echo test"))
        # The conversation handler receives "/echo test" as the text at step 0
        assert "Got name" in response.text

    def test_conversation_does_not_affect_other_users(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        # u2 should still get the regular command
        response = cmd.handle(BotMessage(user_id="u2", text="/echo hi"))
        assert response.text == "echo:u2:hi"

    def test_conversation_cleanup_after_completion(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)
        cmd.register_conversation("single", _single_step_conversation_handler)

        state = ConversationState(kind="single")
        cmd.start_conversation("u1", state)

        # Conversation completes immediately (returns None state)
        r1 = cmd.handle(BotMessage(user_id="u1", text="data"))
        assert r1.text == "done:data"

        # Now the conversation is gone, regular commands should work
        r2 = cmd.handle(BotMessage(user_id="u1", text="/echo after"))
        assert r2.text == "echo:u1:after"

    def test_unregistered_conversation_kind_returns_unknown(self) -> None:
        cmd = Commander()
        # Start a conversation with an unregistered kind
        state = ConversationState(kind="nonexistent")
        cmd.start_conversation("u1", state)

        response = cmd.handle(BotMessage(user_id="u1", text="hello"))
        assert response.text == ERR_UNKNOWN_COMMAND


# ---------------------------------------------------------------------------
# Commander: Conversation Cancel
# ---------------------------------------------------------------------------


class TestConversationCancel:
    """Tests for cancelling active conversations."""

    def test_cancel_active_conversation(self) -> None:
        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        response = cmd.handle(BotMessage(user_id="u1", text="/cancel"))
        assert response.text == ERR_OPERATION_CANCELLED

    def test_cancel_custom_text(self) -> None:
        cmd = Commander(cancelled_text="Aborted.")
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        response = cmd.handle(BotMessage(user_id="u1", text="/cancel"))
        assert response.text == "Aborted."

    def test_cancel_case_insensitive(self) -> None:
        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        response = cmd.handle(BotMessage(user_id="u1", text="/CANCEL"))
        assert response.text == ERR_OPERATION_CANCELLED

    def test_cancel_with_whitespace(self) -> None:
        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        response = cmd.handle(BotMessage(user_id="u1", text="  /cancel  "))
        assert response.text == ERR_OPERATION_CANCELLED

    def test_custom_cancel_command(self) -> None:
        cmd = Commander(cancel_command="/abort")
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        # Default /cancel should NOT cancel
        r1 = cmd.handle(BotMessage(user_id="u1", text="/cancel"))
        # The handler gets "/cancel" as text at step 0
        assert r1.text == "Got name. Send confirmation."

        # /abort should cancel
        r2 = cmd.handle(BotMessage(user_id="u1", text="/abort"))
        assert r2.text == ERR_OPERATION_CANCELLED

    def test_after_cancel_commands_work(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        cmd.handle(BotMessage(user_id="u1", text="/cancel"))

        response = cmd.handle(BotMessage(user_id="u1", text="/echo back"))
        assert response.text == "echo:u1:back"


# ---------------------------------------------------------------------------
# Commander: Conversation Expiry
# ---------------------------------------------------------------------------


class TestConversationExpiry:
    """Tests for expired conversation cleanup."""

    def test_expired_conversation_returns_expired_text(self) -> None:
        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler)

        # Create already-expired state
        state = ConversationState(kind="wizard", expires_at=time.time() - 10)
        cmd.start_conversation("u1", state)

        response = cmd.handle(BotMessage(user_id="u1", text="hello"))
        assert response.text == ERR_CONVERSATION_EXPIRED

    def test_expired_conversation_custom_text(self) -> None:
        cmd = Commander(expired_text="Timed out.")
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard", expires_at=time.time() - 10)
        cmd.start_conversation("u1", state)

        response = cmd.handle(BotMessage(user_id="u1", text="hello"))
        assert response.text == "Timed out."

    def test_after_expiry_commands_work(self) -> None:
        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard", expires_at=time.time() - 10)
        cmd.start_conversation("u1", state)

        # First call cleans up and returns expired message
        cmd.handle(BotMessage(user_id="u1", text="hello"))

        # Next call should route to commands
        response = cmd.handle(BotMessage(user_id="u1", text="/echo back"))
        assert response.text == "echo:u1:back"

    def test_non_expired_conversation_continues(self) -> None:
        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler)

        # Far-future expiry
        state = ConversationState(kind="wizard", expires_at=time.time() + 9999)
        cmd.start_conversation("u1", state)

        response = cmd.handle(BotMessage(user_id="u1", text="Alice"))
        assert response.text == "Got name. Send confirmation."


# ---------------------------------------------------------------------------
# Commander: Confirmed Sentinel Callback
# ---------------------------------------------------------------------------


class TestConfirmedSentinelCallback:
    """Tests for the on_confirmed callback when conversation emits confirmed sentinel."""

    def test_confirmed_calls_on_confirmed_callback(self) -> None:
        results: list[dict] = []

        def on_confirmed(data: dict) -> BotResponse:
            results.append(data)
            return BotResponse(text=f"Executed with {data.get('name')}")

        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler, on_confirmed=on_confirmed)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        # Step 0: provide name
        cmd.handle(BotMessage(user_id="u1", text="Alice"))

        # Step 1: confirm with "yes"
        response = cmd.handle(BotMessage(user_id="u1", text="yes"))
        assert response.text == "Executed with Alice"
        assert len(results) == 1
        assert results[0]["name"] == "Alice"
        assert results[0]["confirmed"] is True

    def test_no_on_confirmed_returns_sentinel_response(self) -> None:
        """When on_confirmed is None, the confirmed sentinel response is returned as-is."""
        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        cmd.handle(BotMessage(user_id="u1", text="Alice"))
        response = cmd.handle(BotMessage(user_id="u1", text="yes"))
        assert response.text == CONFIRMED_SENTINEL

    def test_non_confirmed_finish_does_not_call_callback(self) -> None:
        callback_called = False

        def on_confirmed(data: dict) -> BotResponse:
            nonlocal callback_called
            callback_called = True
            return BotResponse(text="should not happen")

        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler, on_confirmed=on_confirmed)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        cmd.handle(BotMessage(user_id="u1", text="Alice"))
        response = cmd.handle(BotMessage(user_id="u1", text="no"))
        assert response.text == "Cancelled by user."
        assert callback_called is False

    def test_confirmed_cleans_up_conversation(self) -> None:
        def on_confirmed(data: dict) -> BotResponse:
            return BotResponse(text="done")

        cmd = Commander()
        cmd.register_command("/echo", _echo_handler)
        cmd.register_conversation("wizard", _simple_conversation_handler, on_confirmed=on_confirmed)

        state = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state)

        cmd.handle(BotMessage(user_id="u1", text="Alice"))
        cmd.handle(BotMessage(user_id="u1", text="yes"))

        # Conversation should be cleaned up, commands work
        response = cmd.handle(BotMessage(user_id="u1", text="/echo after"))
        assert response.text == "echo:u1:after"


# ---------------------------------------------------------------------------
# Commander: Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_multiple_users_independent_conversations(self) -> None:
        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state1 = ConversationState(kind="wizard")
        state2 = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state1)
        cmd.start_conversation("u2", state2)

        r1 = cmd.handle(BotMessage(user_id="u1", text="Alice"))
        r2 = cmd.handle(BotMessage(user_id="u2", text="Bob"))

        assert r1.text == "Got name. Send confirmation."
        assert r2.text == "Got name. Send confirmation."

    def test_start_conversation_replaces_existing(self) -> None:
        cmd = Commander()
        cmd.register_conversation("wizard", _simple_conversation_handler)

        state1 = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state1)
        cmd.handle(BotMessage(user_id="u1", text="Alice"))

        # Start a new conversation, should replace the old one at step 0
        state2 = ConversationState(kind="wizard")
        cmd.start_conversation("u1", state2)

        response = cmd.handle(BotMessage(user_id="u1", text="Bob"))
        assert response.text == "Got name. Send confirmation."

    def test_handle_returns_bot_response(self) -> None:
        cmd = Commander()
        response = cmd.handle(BotMessage(user_id="u1", text="/anything"))
        assert isinstance(response, BotResponse)
