"""Data transfer objects for bot integration."""

from dataclasses import dataclass
from typing import Literal

BotType = Literal["none", "telegram", "xmpp"]


@dataclass(frozen=True)
class Attachment:
    """File attachment detected in a message."""

    url: str
    filename: str = ""
    mime_type: str = ""


@dataclass(frozen=True)
class BotMessage:
    """Normalized incoming message from any bot adapter."""

    user_id: str
    text: str
    attachments: tuple[Attachment, ...] = ()


@dataclass(frozen=True)
class BotResponse:
    """Response to send back to a user."""

    text: str
    audio_path: str = ""
