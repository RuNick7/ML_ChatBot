import os
from dotenv import load_dotenv

load_dotenv()

TG_API_ID = int(os.environ["TG_API_ID"])
TG_API_HASH = os.environ["TG_API_HASH"]
TG_PHONE = os.environ["TG_PHONE"]

BOT_TOKEN = os.environ["BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

TARGET_TAG = os.getenv("TARGET_TAG", "@Kairachat_bot")
RESPONSE_PROBABILITY = float(os.getenv("RESPONSE_PROBABILITY", "0.30"))
COOLDOWN_MINUTES = int(os.getenv("COOLDOWN_MINUTES", "45"))
ACTIVE_HOURS_START = int(os.getenv("ACTIVE_HOURS_START", "9"))
ACTIVE_HOURS_END = int(os.getenv("ACTIVE_HOURS_END", "25"))
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

SESSION_NAME = "userbot_session"
