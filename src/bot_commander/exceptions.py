"""Exception hierarchy for bot-commander."""


class BotCommanderError(Exception):
    """Base exception for all bot-commander errors."""


class ConfigurationError(BotCommanderError):
    """Raised when there is a configuration problem."""


class AdapterError(BotCommanderError):
    """Raised when an adapter encounters an error."""


class AdapterNotFoundError(AdapterError):
    """Raised when a requested adapter is not available."""


class NotInitializedError(BotCommanderError):
    """Raised when a component is used before initialization."""


class CommandError(BotCommanderError):
    """Raised when a command encounters an error."""


class ConversationError(BotCommanderError):
    """Raised when a conversation encounters an error."""
