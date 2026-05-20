import asyncio
import logging

import config
import database as db
from userbot.client import client
import userbot.client as ub_client
from userbot.monitor import register_handlers
from admin_bot.bot import start_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def start_userbot():
    await client.start(phone=config.TG_PHONE)
    me = await client.get_me()
    ub_client.bot_username = me.username or ""
    ub_client.bot_id = me.id
    logger.info("Userbot started as @%s (id=%d)", ub_client.bot_username, ub_client.bot_id)
    register_handlers()
    await client.run_until_disconnected()


async def main():
    db.init_db()
    await asyncio.gather(
        start_userbot(),
        start_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
