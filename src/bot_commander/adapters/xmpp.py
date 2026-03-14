"""XMPP bot adapter."""

import asyncio
import logging
import mimetypes
import os
import threading
from posixpath import basename as url_basename
from urllib.parse import unquote, urlparse
from xml.etree.ElementTree import Element

from bot_commander.config.constants import (
    KEY_ALLOWED_JIDS,
    KEY_DEFAULT_RECEIVER,
    KEY_JID,
    KEY_PASSWORD,
)
from bot_commander.types import Attachment, BotMessage

from .base import BotAdapter, BotConfigProvider

try:
    from xmpp_bot import Settings as XmppSettings
    from xmpp_bot import XmppBot

    XMPP_AVAILABLE = True
except ImportError:
    XMPP_AVAILABLE = False

logger = logging.getLogger(__name__)


class XmppAdapter(BotAdapter):
    """Adapter for xmpp-bot library."""

    def __init__(self) -> None:
        super().__init__()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    def initialize(self, config: BotConfigProvider) -> None:
        """Initialize the XMPP bot connection."""
        if not XMPP_AVAILABLE:
            raise ImportError("xmpp-bot package is not installed")

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        future = asyncio.run_coroutine_threadsafe(self._async_init(config), self._loop)
        future.result(timeout=30)
        logger.info("XMPP bot initialized")

    def _run_loop(self) -> None:
        """Run the asyncio event loop in a daemon thread."""
        asyncio.set_event_loop(self._loop)
        try:
            if self._loop:
                self._loop.run_forever()
        except Exception:
            logger.error("XMPP event loop crashed", exc_info=True)

    async def _async_init(self, config: BotConfigProvider) -> None:
        """Perform async initialization of the XMPP bot."""
        bot = XmppBot.get_instance()

        jid = config.get_bot_setting(KEY_JID)
        password = config.get_bot_setting(KEY_PASSWORD)
        default_receiver = config.get_bot_setting(KEY_DEFAULT_RECEIVER)
        allowed_jids_str = config.get_bot_setting(KEY_ALLOWED_JIDS)

        allowed_jids: frozenset[str] = frozenset()
        if allowed_jids_str:
            allowed_jids = frozenset(j.strip() for j in allowed_jids_str.split(","))

        settings = XmppSettings(
            jid=jid,
            password=password,
            default_receiver=default_receiver,
            allowed_jids=allowed_jids,
        )
        await bot.initialize(settings=settings)
        bot.add_message_handler("bot_commander", self._handle_message)

    async def _handle_message(self, sender: str, message: str, stanza: object) -> None:
        """Convert an XMPP message into a BotMessage and forward it."""
        bare_jid = sender.split("/")[0]
        attachments = _extract_attachments(stanza)
        msg = BotMessage(user_id=bare_jid, text=message, attachments=attachments)
        if self._on_message:
            self._on_message(msg)

    def reply(self, user_id: str, text: str) -> None:
        """Send a reply to an XMPP user."""
        if XMPP_AVAILABLE and self._loop:
            asyncio.run_coroutine_threadsafe(
                XmppBot.get_instance().reply_to_user(text, user_id),
                self._loop,
            )

    def send_audio_file(self, user_id: str, audio_path: str) -> None:
        """Send an audio file to an XMPP user via HTTP File Upload."""
        if XMPP_AVAILABLE and self._loop:
            future = asyncio.run_coroutine_threadsafe(
                XmppBot.get_instance().send_audio_file(audio_path, user_id),
                self._loop,
            )
            future.add_done_callback(
                lambda f: _on_audio_sent(f, audio_path, user_id)
            )

    def shutdown(self) -> None:
        """Shutdown the XMPP bot connection."""
        if XMPP_AVAILABLE:
            try:
                XmppBot.get_instance().disconnect()
                if self._loop:
                    self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception as e:
                logger.error("Error shutting down XMPP bot: %s", e, exc_info=True)


_OOB_NS = "jabber:x:oob"


def _extract_attachments(stanza: object) -> tuple[Attachment, ...]:
    """Extract file attachments from an XMPP stanza via OOB (XEP-0066).

    Parses the raw XML for ``<x xmlns="jabber:x:oob"><url>`` elements.
    Falls back gracefully when the stanza has no XML or no OOB data.
    """
    xml: Element | None = getattr(stanza, "xml", None)
    if xml is None:
        return ()

    attachments: list[Attachment] = []
    for x_elem in xml.findall(f"{{{_OOB_NS}}}x"):
        url_elem = x_elem.find(f"{{{_OOB_NS}}}url")
        if url_elem is None or not url_elem.text:
            continue
        url = url_elem.text.strip()
        if not url:
            continue

        # Derive filename from URL path
        parsed = urlparse(url)
        filename = unquote(url_basename(parsed.path)) if parsed.path else ""

        # Guess MIME type from filename
        mime_type, _ = mimetypes.guess_type(filename) if filename else ("", None)

        attachments.append(
            Attachment(url=url, filename=filename, mime_type=mime_type or "")
        )

    return tuple(attachments)


def _on_audio_sent(
    future: asyncio.Future,  # type: ignore[type-arg]
    audio_path: str,
    user_id: str,
) -> None:
    """Callback after audio upload completes — log errors and clean up."""
    exc = future.exception()
    if exc:
        logger.error("Failed to send audio file to %s: %s", user_id, exc)
    try:
        os.unlink(audio_path)
    except OSError:
        logger.warning("Failed to delete temp audio file: %s", audio_path)
