"""Tests for bot_commander.conversation."""

import time

from bot_commander.config.constants import CONFIRMED_SENTINEL, DEFAULT_CONVERSATION_TIMEOUT
from bot_commander.conversation import (
    ConversationState,
    confirmed_response,
    is_confirmed,
    is_confirmed_sentinel,
    is_skip,
    is_valid_time,
)
from bot_commander.types import BotResponse


class TestConversationState:
    """Tests for the ConversationState dataclass."""

    def test_create_default(self) -> None:
        state = ConversationState(kind="test_wizard")
        assert state.kind == "test_wizard"
        assert state.step == 0
        assert state.data == {}
        assert state.expires_at > time.time()

    def test_create_with_step_and_data(self) -> None:
        state = ConversationState(kind="edit", step=3, data={"key": "value"})
        assert state.step == 3
        assert state.data == {"key": "value"}

    def test_is_expired_false_for_new_state(self) -> None:
        state = ConversationState(kind="test")
        assert state.is_expired() is False

    def test_is_expired_true_for_past_expiry(self) -> None:
        state = ConversationState(kind="test", expires_at=time.time() - 1)
        assert state.is_expired() is True

    def test_default_timeout_uses_constant(self) -> None:
        before = time.time()
        state = ConversationState(kind="test")
        after = time.time()
        expected_min = before + DEFAULT_CONVERSATION_TIMEOUT
        expected_max = after + DEFAULT_CONVERSATION_TIMEOUT
        assert expected_min <= state.expires_at <= expected_max

    def test_mutable_step(self) -> None:
        state = ConversationState(kind="wizard")
        state.step = 5
        assert state.step == 5

    def test_mutable_data(self) -> None:
        state = ConversationState(kind="wizard")
        state.data["name"] = "test_task"
        assert state.data["name"] == "test_task"

    def test_separate_data_dicts(self) -> None:
        """Each instance should have its own data dict."""
        s1 = ConversationState(kind="a")
        s2 = ConversationState(kind="b")
        s1.data["x"] = 1
        assert "x" not in s2.data


class TestIsSkip:
    """Tests for the is_skip utility function."""

    def test_skip_word(self) -> None:
        assert is_skip("skip") is True

    def test_skip_uppercase(self) -> None:
        assert is_skip("SKIP") is True

    def test_skip_mixed_case(self) -> None:
        assert is_skip("Skip") is True

    def test_none_word(self) -> None:
        assert is_skip("none") is True

    def test_none_uppercase(self) -> None:
        assert is_skip("NONE") is True

    def test_empty_string(self) -> None:
        assert is_skip("") is True

    def test_regular_text(self) -> None:
        assert is_skip("hello") is False

    def test_whitespace_only(self) -> None:
        # Whitespace is not in the skip set (no strip)
        assert is_skip("  ") is False


class TestIsValidTime:
    """Tests for the is_valid_time utility function."""

    def test_valid_midnight(self) -> None:
        assert is_valid_time("00:00") is True

    def test_valid_noon(self) -> None:
        assert is_valid_time("12:00") is True

    def test_valid_end_of_day(self) -> None:
        assert is_valid_time("23:59") is True

    def test_valid_morning(self) -> None:
        assert is_valid_time("09:30") is True

    def test_invalid_hour_24(self) -> None:
        assert is_valid_time("24:00") is False

    def test_invalid_minute_60(self) -> None:
        assert is_valid_time("12:60") is False

    def test_invalid_format_single_digit(self) -> None:
        assert is_valid_time("9:30") is False

    def test_invalid_format_no_colon(self) -> None:
        assert is_valid_time("0930") is False

    def test_invalid_format_text(self) -> None:
        assert is_valid_time("noon") is False

    def test_empty_string(self) -> None:
        assert is_valid_time("") is False

    def test_invalid_format_extra_chars(self) -> None:
        assert is_valid_time("09:30:00") is False


class TestIsConfirmed:
    """Tests for the is_confirmed utility function."""

    def test_confirmed_with_sentinel(self) -> None:
        resp = BotResponse(text=CONFIRMED_SENTINEL)
        assert is_confirmed(resp) is True

    def test_not_confirmed_with_text(self) -> None:
        resp = BotResponse(text="some message")
        assert is_confirmed(resp) is False

    def test_not_confirmed_with_whitespace(self) -> None:
        resp = BotResponse(text=" ")
        assert is_confirmed(resp) is False


class TestConfirmedResponse:
    """Tests for the confirmed_response utility function."""

    def test_creates_sentinel_response(self) -> None:
        resp = confirmed_response()
        assert resp.text == CONFIRMED_SENTINEL
        assert is_confirmed(resp) is True

    def test_returns_bot_response(self) -> None:
        resp = confirmed_response()
        assert isinstance(resp, BotResponse)


class TestIsConfirmedSentinel:
    """Tests for the is_confirmed_sentinel utility function."""

    def test_sentinel_value(self) -> None:
        assert is_confirmed_sentinel(CONFIRMED_SENTINEL) is True

    def test_non_sentinel_value(self) -> None:
        assert is_confirmed_sentinel("hello") is False

    def test_whitespace_is_not_sentinel(self) -> None:
        assert is_confirmed_sentinel(" ") is False

    def test_empty_matches_sentinel(self) -> None:
        # CONFIRMED_SENTINEL is "" so empty string should match
        assert is_confirmed_sentinel("") is True
