"""Telegram bot adapter."""

import logging
import os

from bot_commander.config.constants import (
    KEY_ALLOWED_USER_IDS,
    KEY_BOT_TOKEN,
    KEY_CHANNEL_ID,
)
from bot_commander.types import BotMessage

from .base import BotAdapter, BotConfigProvider

try:
    from telegram_bot import Settings as TelegramSettings
    from telegram_bot import TelegramBot

    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

logger = logging.getLogger(__name__)


class TelegramAdapter(BotAdapter):
    """Adapter for telegram-bot library."""

    def __init__(self) -> None:
        super().__init__()

    def initialize(self, config: BotConfigProvider) -> None:
        """Initialize the Telegram bot connection."""
        if not TELEGRAM_AVAILABLE:
            raise ImportError("telegram-bot package is not installed")

        bot = TelegramBot.get_instance()

        token = config.get_bot_setting(KEY_BOT_TOKEN)
        channel_id = config.get_bot_setting(KEY_CHANNEL_ID)
        allowed_ids_str = config.get_bot_setting(KEY_ALLOWED_USER_IDS)

        allowed_user_ids = None
        if allowed_ids_str:
            allowed_user_ids = {int(uid.strip()) for uid in allowed_ids_str.split(",")}

        settings = TelegramSettings(
            bot_token=token,
            channel_id=channel_id,
            allowed_user_ids=allowed_user_ids,
        )
        bot.initialize(settings=settings)
        bot.add_message_handler(self._handle_update)
        bot.start_receiving()
        logger.info("Telegram bot initialized")

    def _handle_update(self, update: object) -> None:
        """Convert a Telegram update into a BotMessage and forward it."""
        if not getattr(update, "message", None):
            return
        message = update.message  # type: ignore[union-attr]
        if not getattr(message, "text", None):
            return

        msg = BotMessage(
            user_id=str(message.chat_id),  # type: ignore[union-attr]
            text=message.text,  # type: ignore[union-attr]
        )
        if self._on_message:
            self._on_message(msg)

    def reply(self, user_id: str, text: str) -> None:
        """Send a reply to a Telegram user."""
        if TELEGRAM_AVAILABLE:
            TelegramBot.get_instance().reply_to_user(text, int(user_id))

    def send_audio_file(self, user_id: str, audio_path: str) -> None:
        """Send an audio file to a Telegram user as a voice message."""
        if TELEGRAM_AVAILABLE:
            try:
                TelegramBot.get_instance().send_voice_to_user(audio_path, int(user_id))
            finally:
                try:
                    os.unlink(audio_path)
                except OSError:
                    logger.warning("Failed to delete temp audio file: %s", audio_path)

    def shutdown(self) -> None:
        """Shutdown the Telegram bot connection."""
        if TELEGRAM_AVAILABLE:
            try:
                bot = TelegramBot.get_instance()
                bot.flush()
                bot.shutdown()
            except Exception as e:
                logger.error("Error shutting down Telegram bot: %s", e, exc_info=True)
