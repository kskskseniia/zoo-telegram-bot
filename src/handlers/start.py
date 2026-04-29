from pathlib import Path

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

router = Router()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGE_PATH = BASE_DIR / "assets" / "images" / "logo.jpg"


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    photo = FSInputFile(IMAGE_PATH)

    await message.answer_photo(
        photo=photo,
        caption=(
            "🐾 Привет!\n\n"
            "Я помогу тебе узнать твоё тотемное животное "
            "из Московского зоопарка.\n\n"
            "Нажми ниже, чтобы начать викторину!"
        )
    )