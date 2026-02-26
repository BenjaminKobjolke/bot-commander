"""Bot-commander: reusable bot command framework."""

from .adapters.base import BotAdapter, BotConfigProvider
from .commander import Commander, CommandHandler, ConversationHandler, MessageHandler
from .config.constants import CONFIRMED_SENTINEL
from .conversation import (
    ConversationState,
    confirmed_response,
    is_confirmed,
    is_confirmed_sentinel,
    is_skip,
    is_valid_time,
)
from .exceptions import (
    AdapterError,
    AdapterNotFoundError,
    BotCommanderError,
    CommandError,
    ConfigurationError,
    ConversationError,
    NotInitializedError,
)
from .manager import BotManager
from .types import BotMessage, BotResponse, BotType

__all__ = [
    # Adapters
    "BotAdapter",
    "BotConfigProvider",
    # Commander
    "Commander",
    "CommandHandler",
    "ConversationHandler",
    "MessageHandler",
    # Config
    "CONFIRMED_SENTINEL",
    # Conversation
    "ConversationState",
    "confirmed_response",
    "is_confirmed",
    "is_confirmed_sentinel",
    "is_skip",
    "is_valid_time",
    # Exceptions
    "AdapterError",
    "AdapterNotFoundError",
    "BotCommanderError",
    "CommandError",
    "ConfigurationError",
    "ConversationError",
    "NotInitializedError",
    # Manager
    "BotManager",
    # Types
    "BotMessage",
    "BotResponse",
    "BotType",
]

__version__ = "0.1.0"
