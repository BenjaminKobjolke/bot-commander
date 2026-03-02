"""Tests for BotManager lifecycle manager."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from bot_commander.adapters.base import BotAdapter, BotConfigProvider
from bot_commander.commander import MessageHandler
from bot_commander.exceptions import AdapterNotFoundError
from bot_commander.types import BotMessage, BotResponse


class TestBotManagerStart:
    """Tests for BotManager.start()."""

    def test_start_returns_false_when_bot_type_is_none(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        manager = BotManager(message_handler=handler, config_provider=config, bot_type="none")
        result = manager.start()

        assert result is False

    def test_start_creates_telegram_adapter(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        with patch("bot_commander.manager.TelegramAdapter", spec=BotAdapter) as mock_telegram_cls:
            mock_adapter = MagicMock(spec=BotAdapter)
            mock_telegram_cls.return_value = mock_adapter

            manager = BotManager(
                message_handler=handler, config_provider=config, bot_type="telegram"
            )
            result = manager.start()

            assert result is True
            mock_telegram_cls.assert_called_once()
            mock_adapter.set_on_message.assert_called_once()
            mock_adapter.initialize.assert_called_once_with(config)

    def test_start_creates_xmpp_adapter(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        with patch("bot_commander.manager.XmppAdapter", spec=BotAdapter) as mock_xmpp_cls:
            mock_adapter = MagicMock(spec=BotAdapter)
            mock_xmpp_cls.return_value = mock_adapter

            manager = BotManager(message_handler=handler, config_provider=config, bot_type="xmpp")
            result = manager.start()

            assert result is True
            mock_xmpp_cls.assert_called_once()
            mock_adapter.set_on_message.assert_called_once()
            mock_adapter.initialize.assert_called_once_with(config)

    def test_start_raises_adapter_not_found_for_unknown_type(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        manager = BotManager(
            message_handler=handler,
            config_provider=config,
            bot_type="unknown",  # type: ignore[arg-type]
        )

        with pytest.raises(AdapterNotFoundError):
            manager.start()


class TestBotManagerOnMessage:
    """Tests for BotManager._on_message()."""

    def test_on_message_calls_handler_and_replies(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        handler.handle.return_value = BotResponse(text="reply text")
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        with patch("bot_commander.manager.TelegramAdapter", spec=BotAdapter) as mock_telegram_cls:
            mock_adapter = MagicMock(spec=BotAdapter)
            mock_telegram_cls.return_value = mock_adapter

            manager = BotManager(
                message_handler=handler, config_provider=config, bot_type="telegram"
            )
            manager.start()

            message = BotMessage(user_id="user1", text="hello")
            manager._on_message(message)

            handler.handle.assert_called_once_with(message)
            mock_adapter.reply.assert_called_once_with("user1", "reply text")

    def test_on_message_guards_against_empty_response_text(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        handler.handle.return_value = BotResponse(text="")
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        with patch("bot_commander.manager.TelegramAdapter", spec=BotAdapter) as mock_telegram_cls:
            mock_adapter = MagicMock(spec=BotAdapter)
            mock_telegram_cls.return_value = mock_adapter

            manager = BotManager(
                message_handler=handler, config_provider=config, bot_type="telegram"
            )
            manager.start()

            message = BotMessage(user_id="user1", text="hello")
            manager._on_message(message)

            handler.handle.assert_called_once_with(message)
            mock_adapter.reply.assert_not_called()

    def test_on_message_handles_exceptions(self, caplog: pytest.LogCaptureFixture) -> None:
        handler = MagicMock(spec=MessageHandler)
        handler.handle.side_effect = RuntimeError("boom")
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        with patch("bot_commander.manager.TelegramAdapter", spec=BotAdapter) as mock_telegram_cls:
            mock_adapter = MagicMock(spec=BotAdapter)
            mock_telegram_cls.return_value = mock_adapter

            manager = BotManager(
                message_handler=handler, config_provider=config, bot_type="telegram"
            )
            manager.start()

            message = BotMessage(user_id="user1", text="hello")
            with caplog.at_level(logging.ERROR):
                manager._on_message(message)

            assert "boom" in caplog.text
            mock_adapter.reply.assert_not_called()


class TestBotManagerSendMessage:
    """Tests for BotManager.send_message()."""

    def test_send_message_calls_adapter_reply(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        with patch("bot_commander.manager.TelegramAdapter", spec=BotAdapter) as mock_telegram_cls:
            mock_adapter = MagicMock(spec=BotAdapter)
            mock_telegram_cls.return_value = mock_adapter

            manager = BotManager(
                message_handler=handler, config_provider=config, bot_type="telegram"
            )
            manager.start()
            manager.send_message("user1", "Hello from outside")

            mock_adapter.reply.assert_called_once_with("user1", "Hello from outside")

    def test_send_message_no_adapter_does_nothing(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        manager = BotManager(message_handler=handler, config_provider=config, bot_type="none")
        # Should not raise any exception
        manager.send_message("user1", "Hello")


class TestBotManagerShutdown:
    """Tests for BotManager.shutdown()."""

    def test_shutdown_calls_adapter_shutdown(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        with patch("bot_commander.manager.TelegramAdapter", spec=BotAdapter) as mock_telegram_cls:
            mock_adapter = MagicMock(spec=BotAdapter)
            mock_telegram_cls.return_value = mock_adapter

            manager = BotManager(
                message_handler=handler, config_provider=config, bot_type="telegram"
            )
            manager.start()
            manager.shutdown()

            mock_adapter.shutdown.assert_called_once()

    def test_shutdown_handles_no_adapter_gracefully(self) -> None:
        handler = MagicMock(spec=MessageHandler)
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        manager = BotManager(message_handler=handler, config_provider=config, bot_type="none")
        # Should not raise any exception
        manager.shutdown()

    def test_shutdown_catches_exceptions(self, caplog: pytest.LogCaptureFixture) -> None:
        handler = MagicMock(spec=MessageHandler)
        config = MagicMock(spec=BotConfigProvider)
        from bot_commander.manager import BotManager

        with patch("bot_commander.manager.TelegramAdapter", spec=BotAdapter) as mock_telegram_cls:
            mock_adapter = MagicMock(spec=BotAdapter)
            mock_adapter.shutdown.side_effect = RuntimeError("shutdown error")
            mock_telegram_cls.return_value = mock_adapter

            manager = BotManager(
                message_handler=handler, config_provider=config, bot_type="telegram"
            )
            manager.start()

            with caplog.at_level(logging.ERROR):
                manager.shutdown()

            assert "shutdown error" in caplog.text
