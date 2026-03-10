"""Tests for bot_commander.types."""

import pytest

from bot_commander.types import Attachment, BotMessage, BotResponse


class TestBotMessage:
    """Tests for the BotMessage dataclass."""

    def test_create_bot_message(self) -> None:
        msg = BotMessage(user_id="user123", text="hello")
        assert msg.user_id == "user123"
        assert msg.text == "hello"

    def test_bot_message_is_frozen(self) -> None:
        msg = BotMessage(user_id="user123", text="hello")
        with pytest.raises(AttributeError):
            msg.user_id = "other"  # type: ignore[misc]
        with pytest.raises(AttributeError):
            msg.text = "other"  # type: ignore[misc]

    def test_bot_message_equality(self) -> None:
        msg1 = BotMessage(user_id="u1", text="hi")
        msg2 = BotMessage(user_id="u1", text="hi")
        msg3 = BotMessage(user_id="u2", text="hi")
        assert msg1 == msg2
        assert msg1 != msg3

    def test_bot_message_repr(self) -> None:
        msg = BotMessage(user_id="u1", text="hi")
        r = repr(msg)
        assert "BotMessage" in r
        assert "u1" in r
        assert "hi" in r

    def test_bot_message_empty_fields(self) -> None:
        msg = BotMessage(user_id="", text="")
        assert msg.user_id == ""
        assert msg.text == ""

    def test_bot_message_default_no_attachments(self) -> None:
        msg = BotMessage(user_id="u1", text="hi")
        assert msg.attachments == ()

    def test_bot_message_with_attachments(self) -> None:
        att = Attachment(
            url="https://example.com/file.ogg", filename="file.ogg", mime_type="audio/ogg"
        )
        msg = BotMessage(user_id="u1", text="hi", attachments=(att,))
        assert len(msg.attachments) == 1
        assert msg.attachments[0].url == "https://example.com/file.ogg"

    def test_bot_message_backwards_compatible(self) -> None:
        """Existing BotMessage(user_id=..., text=...) calls still work."""
        msg = BotMessage(user_id="u1", text="hi")
        assert msg.attachments == ()


class TestAttachment:
    """Tests for the Attachment dataclass."""

    def test_create_attachment(self) -> None:
        att = Attachment(
            url="https://example.com/voice.ogg", filename="voice.ogg", mime_type="audio/ogg"
        )
        assert att.url == "https://example.com/voice.ogg"
        assert att.filename == "voice.ogg"
        assert att.mime_type == "audio/ogg"

    def test_attachment_defaults(self) -> None:
        att = Attachment(url="https://example.com/file")
        assert att.filename == ""
        assert att.mime_type == ""

    def test_attachment_is_frozen(self) -> None:
        att = Attachment(url="https://example.com/file")
        with pytest.raises(AttributeError):
            att.url = "other"  # type: ignore[misc]

    def test_attachment_equality(self) -> None:
        a1 = Attachment(url="https://example.com/a", filename="a")
        a2 = Attachment(url="https://example.com/a", filename="a")
        a3 = Attachment(url="https://example.com/b", filename="b")
        assert a1 == a2
        assert a1 != a3


class TestBotResponse:
    """Tests for the BotResponse dataclass."""

    def test_create_bot_response(self) -> None:
        resp = BotResponse(text="ok")
        assert resp.text == "ok"

    def test_bot_response_is_frozen(self) -> None:
        resp = BotResponse(text="ok")
        with pytest.raises(AttributeError):
            resp.text = "other"  # type: ignore[misc]

    def test_bot_response_equality(self) -> None:
        r1 = BotResponse(text="a")
        r2 = BotResponse(text="a")
        r3 = BotResponse(text="b")
        assert r1 == r2
        assert r1 != r3

    def test_bot_response_empty_text(self) -> None:
        resp = BotResponse(text="")
        assert resp.text == ""

    def test_bot_response_repr(self) -> None:
        resp = BotResponse(text="done")
        r = repr(resp)
        assert "BotResponse" in r
        assert "done" in r
