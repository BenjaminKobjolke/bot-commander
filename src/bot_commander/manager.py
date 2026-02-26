"""Bot lifecycle manager - factory and coordinator."""

from __future__ import annotations

import logging

from .adapters.base import BotAdapter, BotConfigProvider
from .adapters.telegram import TelegramAdapter
from .adapters.xmpp import XmppAdapter
from .commander import MessageHandler
from .config.constants import LOG_BOT_DISABLED, LOG_BOT_STARTED, LOG_BOT_STOPPED
from .exceptions import AdapterNotFoundError
from .types import BotMessage, BotType

logger = logging.getLogger(__name__)


class BotManager:
    """Factory and lifecycle manager for bot integration."""

    def __init__(
        self,
        message_handler: MessageHandler,
        config_provider: BotConfigProvider,
        bot_type: BotType,
    ) -> None:
        self._message_handler = message_handler
        self._config_provider = config_provider
        self._bot_type = bot_type
        self._adapter: BotAdapter | None = None

    def start(self) -> bool:
        """Start the bot adapter.

        Returns
        -------
        bool
            True if the bot was started, False if disabled (type=none).

        Raises
        ------
        AdapterNotFoundError
            If the bot_type is not recognized.
        """
        if self._bot_type == "none":
            logger.info(LOG_BOT_DISABLED)
            return False

        if self._bot_type == "telegram":
            self._adapter = TelegramAdapter()
        elif self._bot_type == "xmpp":
            self._adapter = XmppAdapter()
        else:
            raise AdapterNotFoundError(f"Unknown bot type: {self._bot_type}")

        self._adapter.set_on_message(self._on_message)
        self._adapter.initialize(self._config_provider)
        logger.info(LOG_BOT_STARTED.format(self._bot_type))
        return True

    def _on_message(self, message: BotMessage) -> None:
        """Handle an incoming bot message."""
        try:
            response = self._message_handler.handle(message)
            if response.text and self._adapter:
                self._adapter.reply(message.user_id, response.text)
        except Exception:
            logger.error("Error processing bot message", exc_info=True)

    def shutdown(self) -> None:
        """Shutdown the bot adapter."""
        if self._adapter:
            try:
                self._adapter.shutdown()
                logger.info(LOG_BOT_STOPPED)
            except Exception:
                logger.error("Error shutting down bot", exc_info=True)
