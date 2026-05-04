import asyncio
import logging

from aiogram import Bot, Dispatcher

from src.config import BOT_TOKEN
from src.logger import setup_logger
from src.handlers.start import router as start_router
from src.handlers.quiz import router as quiz_router

async def main() -> None:
    setup_logger()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(quiz_router)

    logging.info("Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())