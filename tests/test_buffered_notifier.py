"""Tests for BufferedNotifier — rate-limited message batching."""

import time
from unittest.mock import MagicMock

from bot_commander.buffered_notifier import BufferedNotifier


class TestBufferedNotifierSingleMessage:
    """First message should be sent immediately (no buffering delay)."""

    def test_single_message_sent_immediately(self) -> None:
        send_fn = MagicMock()
        notifier = BufferedNotifier(send_fn=send_fn, interval=1.5)

        notifier.send("user1", "Hello")

        send_fn.assert_called_once_with("user1", "Hello")


class TestBufferedNotifierBatching:
    """Rapid messages within the interval should be batched."""

    def test_rapid_messages_batched_on_flush(self) -> None:
        """Multiple messages sent rapidly are combined into one on flush."""
        send_fn = MagicMock()
        notifier = BufferedNotifier(send_fn=send_fn, interval=10.0)

        notifier.send("user1", "Line 1")
        send_fn.reset_mock()  # Clear the first immediate send

        notifier.send("user1", "Line 2")
        notifier.send("user1", "Line 3")

        # Lines 2 and 3 should be buffered, not sent yet
        send_fn.assert_not_called()

        notifier.flush("user1")
        send_fn.assert_called_once_with("user1", "Line 2\nLine 3")


class TestBufferedNotifierFlush:
    """flush() sends all remaining buffered messages."""

    def test_flush_sends_remaining_buffer(self) -> None:
        send_fn = MagicMock()
        notifier = BufferedNotifier(send_fn=send_fn, interval=10.0)

        notifier.send("user1", "First")
        send_fn.reset_mock()

        notifier.send("user1", "Buffered line")
        notifier.flush("user1")

        send_fn.assert_called_once_with("user1", "Buffered line")

    def test_flush_all_users(self) -> None:
        """flush() without user_id flushes all users."""
        send_fn = MagicMock()
        notifier = BufferedNotifier(send_fn=send_fn, interval=10.0)

        notifier.send("user1", "A")
        notifier.send("user2", "B")
        send_fn.reset_mock()

        notifier.send("user1", "A2")
        notifier.send("user2", "B2")
        notifier.flush()

        calls = send_fn.call_args_list
        assert len(calls) == 2
        # Order may vary, check both users got their messages
        sent = {c.args[0]: c.args[1] for c in calls}
        assert sent["user1"] == "A2"
        assert sent["user2"] == "B2"

    def test_flush_empty_buffer_does_nothing(self) -> None:
        send_fn = MagicMock()
        notifier = BufferedNotifier(send_fn=send_fn, interval=10.0)

        notifier.flush("user1")
        send_fn.assert_not_called()


class TestBufferedNotifierIntervalReset:
    """Messages after the interval elapses should be sent as new immediate messages."""

    def test_messages_after_interval_sent_separately(self) -> None:
        send_fn = MagicMock()
        notifier = BufferedNotifier(send_fn=send_fn, interval=0.05)

        notifier.send("user1", "First")
        send_fn.assert_called_with("user1", "First")

        time.sleep(0.1)  # Wait longer than interval

        notifier.send("user1", "Second")
        assert send_fn.call_count == 2
        send_fn.assert_called_with("user1", "Second")


class TestBufferedNotifierPerUser:
    """Each user has independent buffering."""

    def test_per_user_buffering(self) -> None:
        send_fn = MagicMock()
        notifier = BufferedNotifier(send_fn=send_fn, interval=10.0)

        notifier.send("alice", "Hello Alice")
        notifier.send("bob", "Hello Bob")

        # Both should be sent immediately (first message for each user)
        assert send_fn.call_count == 2
        send_fn.assert_any_call("alice", "Hello Alice")
        send_fn.assert_any_call("bob", "Hello Bob")

    def test_buffering_independent_per_user(self) -> None:
        """Flushing one user doesn't affect another user's buffer."""
        send_fn = MagicMock()
        notifier = BufferedNotifier(send_fn=send_fn, interval=10.0)

        notifier.send("alice", "A1")
        notifier.send("bob", "B1")
        send_fn.reset_mock()

        notifier.send("alice", "A2")
        notifier.send("bob", "B2")

        notifier.flush("alice")
        send_fn.assert_called_once_with("alice", "A2")
        # Bob's buffer should remain
        send_fn.reset_mock()

        notifier.flush("bob")
        send_fn.assert_called_once_with("bob", "B2")


class TestBufferedNotifierTimerFlush:
    """Deferred timer should flush buffered messages automatically."""

    def test_timer_flushes_after_interval(self) -> None:
        send_fn = MagicMock()
        notifier = BufferedNotifier(send_fn=send_fn, interval=0.1)

        notifier.send("user1", "First")
        send_fn.reset_mock()

        notifier.send("user1", "Buffered")

        # Should not be sent yet
        send_fn.assert_not_called()

        # Wait for timer to fire
        time.sleep(0.25)

        send_fn.assert_called_once_with("user1", "Buffered")
