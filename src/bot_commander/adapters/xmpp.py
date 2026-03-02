"""XMPP bot adapter."""

import asyncio
import logging
import threading

from bot_commander.config.constants import (
    KEY_ALLOWED_JIDS,
    KEY_DEFAULT_RECEIVER,
    KEY_JID,
    KEY_PASSWORD,
)
from bot_commander.types import BotMessage

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
        msg = BotMessage(user_id=bare_jid, text=message)
        if self._on_message:
            self._on_message(msg)

    def reply(self, user_id: str, text: str) -> None:
        """Send a reply to an XMPP user."""
        if XMPP_AVAILABLE and self._loop:
            asyncio.run_coroutine_threadsafe(
                XmppBot.get_instance().reply_to_user(text, user_id),
                self._loop,
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
