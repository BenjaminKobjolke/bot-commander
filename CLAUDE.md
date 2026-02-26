# CLAUDE.md

## Project Overview

Reusable bot command framework library providing generic bot infrastructure: types, adapters, command routing, conversation state machines, and lifecycle management. Designed to be used as a dependency by projects that need bot integration (Telegram, XMPP).

## Commands

```bash
# Install dependencies
install.bat

# Run tests
tools\tests.bat

# Or manually
uv run pytest -v
uv run ruff check src/ tests/
```

## Architecture

- `src/bot_commander/types.py` - Core DTOs: BotMessage, BotResponse, BotType
- `src/bot_commander/exceptions.py` - Exception hierarchy (BotCommanderError base)
- `src/bot_commander/config/constants.py` - Sentinel values, config key constants, default messages
- `src/bot_commander/conversation.py` - ConversationState dataclass and utility functions

## Key Implementation Details

- Zero runtime dependencies; adapter extras (telegram, xmpp) are optional
- Frozen dataclasses for DTOs (BotMessage, BotResponse)
- Standard `logging` module (not custom loggers)
- ConversationState uses time-based expiration
- CONFIRMED_SENTINEL used to signal wizard confirmation to callers
- src layout with hatchling build system

## Coding Rules Source

Path: `D:\GIT\BenjaminKobjolke\claude-code\coding-rules`
