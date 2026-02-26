"""Conversation state machine for bot wizards and confirmations."""

import re
import time
from dataclasses import dataclass, field
from typing import Any

from .config.constants import CONFIRMED_SENTINEL, DEFAULT_CONVERSATION_TIMEOUT
from .types import BotResponse


@dataclass
class ConversationState:
    """Per-user conversation state.

    Tracks the current step in a multi-step conversation (wizard, confirmation)
    along with accumulated data and an expiration timestamp.
    """

    kind: str
    step: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    expires_at: float = field(default_factory=lambda: time.time() + DEFAULT_CONVERSATION_TIMEOUT)

    def is_expired(self) -> bool:
        """Check whether this conversation has timed out."""
        return time.time() > self.expires_at


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def is_skip(text: str) -> bool:
    """Return True if the user wants to skip a field."""
    return text.lower() in ("skip", "none", "")


def is_valid_time(text: str) -> bool:
    """Return True if *text* is a valid HH:MM time string."""
    match = re.match(r"^(\d{2}):(\d{2})$", text)
    if not match:
        return False
    hours, minutes = int(match.group(1)), int(match.group(2))
    return 0 <= hours <= 23 and 0 <= minutes <= 59


def is_confirmed(response: BotResponse) -> bool:
    """Return True if *response* carries the confirmed sentinel."""
    return response.text == CONFIRMED_SENTINEL


def confirmed_response() -> BotResponse:
    """Create a BotResponse carrying the confirmed sentinel."""
    return BotResponse(text=CONFIRMED_SENTINEL)


def is_confirmed_sentinel(text: str) -> bool:
    """Return True if *text* equals the confirmed sentinel value."""
    return text == CONFIRMED_SENTINEL
