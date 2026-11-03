# bot-commander

Reusable bot command framework with Telegram and XMPP adapters.

## Installation

```bash
install.bat
```

Or with uv directly:

```bash
uv sync --all-extras
```

## Usage

```python
from bot_commander import BotMessage, BotResponse, BotType
from bot_commander.conversation import ConversationState
from bot_commander.exceptions import BotCommanderError
```

## CLI

Send one message through the configured bot and exit. Non-Python tools can use this to reuse the adapters as a child process:

```bash
uv run --project <bot-commander dir> --all-extras bot-commander notify [--env <file>] --to <chat id or JID> "text"
```

`--env` is optional. Without it, the settings are read from environment variables, so a caller can pass secrets without a file and without putting them on the command line. The env file uses `KEY=VALUE` lines, with the same names as fints-postbank's `.env` files:

| Name | Used for |
|------|----------|
| `BOT_MODE` | `telegram` or `xmpp` (required) |
| `TELEGRAM_BOT_TOKEN` | Telegram (required) |
| `TELEGRAM_CHANNEL_ID`, `TELEGRAM_ALLOWED_USER_IDS` | Telegram (optional) |
| `XMPP_JID`, `XMPP_PASSWORD` | XMPP (required) |
| `XMPP_DEFAULT_RECEIVER`, `XMPP_ALLOWED_JIDS` | XMPP (optional) |

Exit code 0 means the message was sent. Exit code 1 means a config or send error; the reason goes to stderr.

## Optional Adapters

Install with adapter support:

```bash
uv sync --extra telegram   # Telegram adapter
uv sync --extra xmpp       # XMPP adapter
uv sync --all-extras       # All adapters
```

## Development

Run tests:

```bash
tools\tests.bat
```

## Dependencies

- Python >= 3.11
- No runtime dependencies (adapters are optional extras)
- Dev: pytest, ruff
