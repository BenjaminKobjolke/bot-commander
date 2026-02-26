"""Tests for bot_commander.config.constants."""

from bot_commander.config.constants import (
    CONFIRMED_SENTINEL,
    DEFAULT_CONVERSATION_TIMEOUT,
    ERR_COMMAND_DISABLED,
    ERR_CONVERSATION_EXPIRED,
    ERR_OPERATION_CANCELLED,
    ERR_UNKNOWN_COMMAND,
    KEY_ALLOWED_JIDS,
    KEY_ALLOWED_USER_IDS,
    KEY_BOT_TOKEN,
    KEY_CHANNEL_ID,
    KEY_DEFAULT_RECEIVER,
    KEY_JID,
    KEY_PASSWORD,
    LOG_BOT_DISABLED,
    LOG_BOT_STARTED,
    LOG_BOT_STOPPED,
)


class TestSentinels:
    """Tests for sentinel values."""

    def test_confirmed_sentinel_is_empty_string(self) -> None:
        assert CONFIRMED_SENTINEL == ""

    def test_default_conversation_timeout(self) -> None:
        assert DEFAULT_CONVERSATION_TIMEOUT == 300


class TestTelegramAdapterKeys:
    """Tests for Telegram adapter config key constants."""

    def test_bot_token_key(self) -> None:
        assert KEY_BOT_TOKEN == "bot_token"

    def test_channel_id_key(self) -> None:
        assert KEY_CHANNEL_ID == "channel_id"

    def test_allowed_user_ids_key(self) -> None:
        assert KEY_ALLOWED_USER_IDS == "allowed_user_ids"


class TestXmppAdapterKeys:
    """Tests for XMPP adapter config key constants."""

    def test_jid_key(self) -> None:
        assert KEY_JID == "jid"

    def test_password_key(self) -> None:
        assert KEY_PASSWORD == "password"

    def test_default_receiver_key(self) -> None:
        assert KEY_DEFAULT_RECEIVER == "default_receiver"

    def test_allowed_jids_key(self) -> None:
        assert KEY_ALLOWED_JIDS == "allowed_jids"


class TestMessageStrings:
    """Tests for default message strings."""

    def test_unknown_command(self) -> None:
        assert "Unknown command" in ERR_UNKNOWN_COMMAND
        assert "/help" in ERR_UNKNOWN_COMMAND

    def test_command_disabled_has_placeholder(self) -> None:
        assert "{}" in ERR_COMMAND_DISABLED
        formatted = ERR_COMMAND_DISABLED.format("/delete")
        assert "/delete" in formatted

    def test_conversation_expired(self) -> None:
        assert "expired" in ERR_CONVERSATION_EXPIRED.lower()

    def test_operation_cancelled(self) -> None:
        assert "cancelled" in ERR_OPERATION_CANCELLED.lower()


class TestLogStrings:
    """Tests for log message strings."""

    def test_bot_disabled(self) -> None:
        assert "disabled" in LOG_BOT_DISABLED.lower()

    def test_bot_started_has_placeholder(self) -> None:
        assert "{}" in LOG_BOT_STARTED
        formatted = LOG_BOT_STARTED.format("telegram")
        assert "telegram" in formatted

    def test_bot_stopped(self) -> None:
        assert "stopped" in LOG_BOT_STOPPED.lower()
