from telethon import TelegramClient
import config

client = TelegramClient(
    config.SESSION_NAME,
    config.TG_API_ID,
    config.TG_API_HASH,
)

# Заполняется в main.py после client.start()
bot_username: str = ""
bot_id: int = 0
