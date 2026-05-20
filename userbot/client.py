from telethon import TelegramClient
from telethon.sessions import StringSession
import config

if config.SESSION_STRING:
    _session = StringSession(config.SESSION_STRING)
else:
    _session = config.SESSION_NAME

client = TelegramClient(
    _session,
    config.TG_API_ID,
    config.TG_API_HASH,
)

bot_username: str = ""
bot_id: int = 0
