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
