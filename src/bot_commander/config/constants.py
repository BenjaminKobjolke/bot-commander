"""Constants for bot-commander."""

# ---------------------------------------------------------------------------
# Sentinel values
# ---------------------------------------------------------------------------

# Sentinel value indicating "confirmed, execute the action".
# Used by conversation wizards when the user says "yes" -- the caller
# checks for this to know it should perform the actual operation.
CONFIRMED_SENTINEL = ""

# ---------------------------------------------------------------------------
# Adapter configuration key constants
# ---------------------------------------------------------------------------

# Telegram adapter keys
KEY_BOT_TOKEN = "bot_token"
KEY_CHANNEL_ID = "channel_id"
KEY_ALLOWED_USER_IDS = "allowed_user_ids"

# XMPP adapter keys
KEY_JID = "jid"
KEY_PASSWORD = "password"
KEY_DEFAULT_RECEIVER = "default_receiver"
KEY_ALLOWED_JIDS = "allowed_jids"

# ---------------------------------------------------------------------------
# CLI env-file names (same names as fints-postbank's .env files)
# ---------------------------------------------------------------------------

ENV_BOT_MODE = "BOT_MODE"
ENV_SETTING_NAMES = {
    KEY_BOT_TOKEN: "TELEGRAM_BOT_TOKEN",
    KEY_CHANNEL_ID: "TELEGRAM_CHANNEL_ID",
    KEY_ALLOWED_USER_IDS: "TELEGRAM_ALLOWED_USER_IDS",
    KEY_JID: "XMPP_JID",
    KEY_PASSWORD: "XMPP_PASSWORD",
    KEY_DEFAULT_RECEIVER: "XMPP_DEFAULT_RECEIVER",
    KEY_ALLOWED_JIDS: "XMPP_ALLOWED_JIDS",
}
# telegram-bot requires a channel id even when only direct messages are sent.
DEFAULT_CHANNEL_ID = "@dummy_channel"
REQUIRED_SETTINGS = {
    "telegram": (KEY_BOT_TOKEN,),
    "xmpp": (KEY_JID, KEY_PASSWORD),
}

# ---------------------------------------------------------------------------
# Conversation defaults
# ---------------------------------------------------------------------------

DEFAULT_CONVERSATION_TIMEOUT = 300  # 5 minutes

# ---------------------------------------------------------------------------
# Default message strings
# ---------------------------------------------------------------------------

ERR_UNKNOWN_COMMAND = "Unknown command. Type /help for available commands."
ERR_COMMAND_DISABLED = "Command {} is disabled by configuration."
ERR_CONVERSATION_EXPIRED = "Session expired. Please start over."
ERR_OPERATION_CANCELLED = "Operation cancelled."

# ---------------------------------------------------------------------------
# Log message strings
# ---------------------------------------------------------------------------

LOG_BOT_DISABLED = "Bot is disabled (type=none)."
LOG_BOT_STARTED = "Bot started (type={})."
LOG_BOT_STOPPED = "Bot stopped."
