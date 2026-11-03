"""Command-line entry point: send one message through the configured bot.

Lets non-Python tools (e.g. postbankcli) reuse the Telegram/XMPP adapters as a child process.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from .config.constants import (
    DEFAULT_CHANNEL_ID,
    ENV_BOT_MODE,
    ENV_SETTING_NAMES,
    KEY_CHANNEL_ID,
    KEY_DEFAULT_RECEIVER,
    REQUIRED_SETTINGS,
)
from .manager import BotManager
from .types import BotMessage, BotResponse

logger = logging.getLogger(__name__)


def parse_env_file(path: Path) -> dict[str, str]:
    """Read KEY=VALUE lines; blank lines and # comments are skipped."""
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


class EnvConfigProvider:
    """BotConfigProvider backed by env-file values."""

    def __init__(self, values: dict[str, str]) -> None:
        self._values = values

    def get_bot_setting(self, key: str, fallback: str = "") -> str:
        env_name = ENV_SETTING_NAMES.get(key)
        value = self._values.get(env_name, "") if env_name else ""
        if not value and key == KEY_CHANNEL_ID:
            return DEFAULT_CHANNEL_ID
        return value or fallback


class _IgnoreMessages:
    """Notify never answers incoming messages."""

    def handle(self, message: BotMessage) -> BotResponse:
        return BotResponse(text="")


def _notify(values: dict[str, str], source: str, to: str, text: str) -> int:
    bot_type = values.get(ENV_BOT_MODE, "").lower()
    if bot_type not in REQUIRED_SETTINGS:
        print(f"{ENV_BOT_MODE} must be telegram or xmpp in {source}", file=sys.stderr)
        return 1
    # xmpp-bot rejects an empty default receiver; the recipient of this message is the natural one.
    receiver_name = ENV_SETTING_NAMES[KEY_DEFAULT_RECEIVER]
    values = {**values, receiver_name: values.get(receiver_name) or to}
    provider = EnvConfigProvider(values)
    missing = [ENV_SETTING_NAMES[key] for key in REQUIRED_SETTINGS[bot_type]
               if not provider.get_bot_setting(key)]
    if missing:
        print(f"Missing in {source}: {', '.join(missing)}", file=sys.stderr)
        return 1

    manager = BotManager(
        message_handler=_IgnoreMessages(), config_provider=provider, bot_type=bot_type
    )
    try:
        manager.start()
        manager.send_message(to, text)
    except Exception as error:
        print(f"Send failed: {error}", file=sys.stderr)
        return 1
    finally:
        manager.shutdown()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bot-commander")
    commands = parser.add_subparsers(dest="command", required=True)
    notify = commands.add_parser("notify", help="Send one message and exit.")
    # Without --env the settings come from environment variables, so callers can pass secrets
    # without writing a file or exposing them on the command line.
    notify.add_argument(
        "--env", type=Path, help="Env file with bot settings (default: environment)."
    )
    notify.add_argument("--to", required=True, help="Telegram chat id or XMPP JID.")
    notify.add_argument("text")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING)
    if args.env is None:
        return _notify(dict(os.environ), "environment", args.to, args.text)
    if not args.env.is_file():
        print(f"Env file not found: {args.env}", file=sys.stderr)
        return 1
    return _notify(parse_env_file(args.env), str(args.env), args.to, args.text)


if __name__ == "__main__":
    sys.exit(main())
