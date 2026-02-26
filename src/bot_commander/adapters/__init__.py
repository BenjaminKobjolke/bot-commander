"""Adapter layer for bot-commander.

Provides the abstract base class and concrete adapters for
Telegram and XMPP bots.
"""

from .base import BotAdapter, BotConfigProvider

__all__ = [
    "BotAdapter",
    "BotConfigProvider",
]
