"""Tests for bot_commander.exceptions."""

from bot_commander.exceptions import (
    AdapterError,
    AdapterNotFoundError,
    BotCommanderError,
    CommandError,
    ConfigurationError,
    ConversationError,
    NotInitializedError,
)


class TestExceptionHierarchy:
    """Tests for the exception hierarchy."""

    def test_base_is_exception(self) -> None:
        assert issubclass(BotCommanderError, Exception)

    def test_configuration_error_inherits_base(self) -> None:
        assert issubclass(ConfigurationError, BotCommanderError)

    def test_adapter_error_inherits_base(self) -> None:
        assert issubclass(AdapterError, BotCommanderError)

    def test_adapter_not_found_inherits_adapter(self) -> None:
        assert issubclass(AdapterNotFoundError, AdapterError)
        assert issubclass(AdapterNotFoundError, BotCommanderError)

    def test_not_initialized_inherits_base(self) -> None:
        assert issubclass(NotInitializedError, BotCommanderError)

    def test_command_error_inherits_base(self) -> None:
        assert issubclass(CommandError, BotCommanderError)

    def test_conversation_error_inherits_base(self) -> None:
        assert issubclass(ConversationError, BotCommanderError)

    def test_raise_and_catch_base(self) -> None:
        try:
            raise ConfigurationError("bad config")
        except BotCommanderError as exc:
            assert str(exc) == "bad config"

    def test_raise_adapter_not_found(self) -> None:
        try:
            raise AdapterNotFoundError("telegram not installed")
        except AdapterError as exc:
            assert str(exc) == "telegram not installed"

    def test_all_exceptions_have_message(self) -> None:
        exceptions = [
            BotCommanderError("base"),
            ConfigurationError("config"),
            AdapterError("adapter"),
            AdapterNotFoundError("not found"),
            NotInitializedError("not init"),
            CommandError("command"),
            ConversationError("conversation"),
        ]
        for exc in exceptions:
            assert str(exc) != ""
