from aiogram import Bot, Dispatcher
from admin_bot.handlers import router
import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)


async def start_bot():
    await dp.start_polling(bot, handle_signals=False)
