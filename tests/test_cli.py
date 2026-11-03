"""Tests for the bot-commander command-line entry point."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bot_commander.cli import EnvConfigProvider, main, parse_env_file
from bot_commander.config.constants import (
    KEY_BOT_TOKEN,
    KEY_CHANNEL_ID,
    KEY_DEFAULT_RECEIVER,
    KEY_JID,
)


def _write_env(tmp_path: Path, content: str) -> Path:
    path = tmp_path / ".env"
    path.write_text(content, encoding="utf-8")
    return path


class TestParseEnvFile:
    def test_reads_key_values_and_skips_comments(self, tmp_path: Path) -> None:
        content = "# comment\n\nBOT_MODE=telegram\nTELEGRAM_BOT_TOKEN = abc:1=2\n"
        path = _write_env(tmp_path, content)

        assert parse_env_file(path) == {"BOT_MODE": "telegram", "TELEGRAM_BOT_TOKEN": "abc:1=2"}


class TestEnvConfigProvider:
    def test_maps_adapter_keys_to_env_names(self) -> None:
        provider = EnvConfigProvider({"TELEGRAM_BOT_TOKEN": "tok", "XMPP_JID": "bot@x"})

        assert provider.get_bot_setting(KEY_BOT_TOKEN) == "tok"
        assert provider.get_bot_setting(KEY_JID) == "bot@x"

    def test_channel_id_falls_back_to_dummy(self) -> None:
        assert EnvConfigProvider({}).get_bot_setting(KEY_CHANNEL_ID) == "@dummy_channel"

    def test_unknown_key_returns_fallback(self) -> None:
        assert EnvConfigProvider({}).get_bot_setting("nope", "x") == "x"


class TestNotify:
    def test_sends_once_and_shuts_down(self, tmp_path: Path) -> None:
        env = _write_env(tmp_path, "BOT_MODE=telegram\nTELEGRAM_BOT_TOKEN=tok\n")
        manager = MagicMock()
        manager.start.return_value = True

        with patch("bot_commander.cli.BotManager", return_value=manager) as manager_cls:
            code = main(["notify", "--env", str(env), "--to", "123", "hello"])

        assert code == 0
        assert manager_cls.call_args.kwargs["bot_type"] == "telegram"
        manager.send_message.assert_called_once_with("123", "hello")
        manager.shutdown.assert_called_once()

    def test_missing_token_exits_1(self, tmp_path: Path) -> None:
        env = _write_env(tmp_path, "BOT_MODE=telegram\n")

        with patch("bot_commander.cli.BotManager") as manager_cls:
            code = main(["notify", "--env", str(env), "--to", "123", "hello"])

        assert code == 1
        manager_cls.assert_not_called()

    def test_console_mode_exits_1(self, tmp_path: Path) -> None:
        env = _write_env(tmp_path, "BOT_MODE=console\n")

        assert main(["notify", "--env", str(env), "--to", "123", "hello"]) == 1

    def test_missing_env_file_exits_1(self, tmp_path: Path) -> None:
        assert main(["notify", "--env", str(tmp_path / "nope"), "--to", "1", "hi"]) == 1

    def test_send_error_exits_1_and_still_shuts_down(self, tmp_path: Path) -> None:
        env = _write_env(tmp_path, "BOT_MODE=xmpp\nXMPP_JID=bot@x\nXMPP_PASSWORD=pw\n")
        manager = MagicMock()
        manager.send_message.side_effect = RuntimeError("boom")

        with patch("bot_commander.cli.BotManager", return_value=manager):
            code = main(["notify", "--env", str(env), "--to", "me@x", "hello"])

        assert code == 1
        manager.shutdown.assert_called_once()

    def test_reads_settings_from_environment_without_env_file(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BOT_MODE", "xmpp")
        monkeypatch.setenv("XMPP_JID", "bot@x")
        monkeypatch.setenv("XMPP_PASSWORD", "pw")
        manager = MagicMock()

        with patch("bot_commander.cli.BotManager", return_value=manager) as manager_cls:
            code = main(["notify", "--to", "me@x", "hello"])

        assert code == 0
        assert manager_cls.call_args.kwargs["bot_type"] == "xmpp"
        manager.send_message.assert_called_once_with("me@x", "hello")

    def test_xmpp_receiver_defaults_to_the_recipient(self, tmp_path: Path) -> None:
        env = _write_env(tmp_path, "BOT_MODE=xmpp\nXMPP_JID=bot@x\nXMPP_PASSWORD=pw\n")
        manager = MagicMock()

        with patch("bot_commander.cli.BotManager", return_value=manager) as manager_cls:
            main(["notify", "--env", str(env), "--to", "me@x", "hello"])

        provider = manager_cls.call_args.kwargs["config_provider"]
        assert provider.get_bot_setting(KEY_DEFAULT_RECEIVER) == "me@x"
