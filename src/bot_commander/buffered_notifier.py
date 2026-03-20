"""Rate-limited message sender that batches rapid messages per user."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

DEFAULT_INTERVAL = 1.5
"""Default minimum seconds between sends per user."""


class BufferedNotifier:
    """Rate-limited message sender that batches rapid messages per user.

    Wraps any ``(user_id, text) -> None`` callable and buffers rapid
    messages per user, flushing them as batched (newline-joined)
    messages after the interval elapses.  The first message for each
    user is sent immediately; subsequent messages within the interval
    are buffered until the interval passes or :meth:`flush` is called.

    Thread-safe via :class:`threading.Lock`.
    """

    def __init__(
        self,
        send_fn: Callable[[str, str], None],
        interval: float = DEFAULT_INTERVAL,
    ) -> None:
        self._send_fn = send_fn
        self._interval = interval
        self._lock = threading.Lock()
        self._buffers: dict[str, list[str]] = {}
        self._last_send: dict[str, float] = {}
        self._timers: dict[str, threading.Timer] = {}

    def send(self, user_id: str, text: str) -> None:
        """Buffer a message for *user_id*.

        Sends immediately if the interval has elapsed since the last
        send for this user; otherwise buffers and schedules a deferred
        flush.
        """
        with self._lock:
            now = time.monotonic()
            last = self._last_send.get(user_id, 0.0)
            elapsed = now - last

            if elapsed >= self._interval:
                # Send any previously buffered lines plus the new one
                buf = self._buffers.pop(user_id, [])
                buf.append(text)
                combined = "\n".join(buf)
                self._last_send[user_id] = now
                self._cancel_timer(user_id)
                self._send_fn(user_id, combined)
            else:
                # Buffer and schedule a deferred flush
                self._buffers.setdefault(user_id, []).append(text)
                if user_id not in self._timers:
                    delay = self._interval - elapsed
                    timer = threading.Timer(delay, self._timer_flush, args=(user_id,))
                    timer.daemon = True
                    timer.start()
                    self._timers[user_id] = timer

    def flush(self, user_id: str | None = None) -> None:
        """Flush buffered messages.

        If *user_id* is given, flush only that user's buffer.
        If ``None``, flush all users.
        """
        with self._lock:
            if user_id is not None:
                self._flush_user(user_id)
            else:
                for uid in list(self._buffers):
                    self._flush_user(uid)

    def _flush_user(self, user_id: str) -> None:
        """Flush a single user's buffer.  Must be called with lock held."""
        self._cancel_timer(user_id)
        buf = self._buffers.pop(user_id, [])
        if buf:
            combined = "\n".join(buf)
            self._last_send[user_id] = time.monotonic()
            self._send_fn(user_id, combined)

    def _timer_flush(self, user_id: str) -> None:
        """Called by a deferred timer to flush a user's buffer."""
        with self._lock:
            self._timers.pop(user_id, None)
            self._flush_user(user_id)

    def _cancel_timer(self, user_id: str) -> None:
        """Cancel a pending timer for *user_id*.  Must be called with lock held."""
        timer = self._timers.pop(user_id, None)
        if timer is not None:
            timer.cancel()
