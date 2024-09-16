from aiogram import Bot, Dispatcher
from aiogram.methods import DeleteWebhook
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties
import asyncio
import logging

from app.handlers import router, db, on_startup, on_shutdown
from config import TOKEN
from app.variables import my_commands

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN, session=AiohttpSession(), 
default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

async def main():
    dp.include_router(router)
    await on_startup(dp)
    await bot.set_my_commands(my_commands)
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())