from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import FSInputFile
from aiogram.types import Message

from src.data.questions import QUESTIONS
from src.states import QuizState
from src.data.animals import ANIMALS
from src.config import ADMIN_ID

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = BASE_DIR / "assets" / "images"

router = Router()


def question_keyboard(question_index: int) -> InlineKeyboardMarkup:
    buttons = []

    for answer_index, answer in enumerate(QUESTIONS[question_index]["answers"]):
        buttons.append([
            InlineKeyboardButton(
                text=answer["text"],
                callback_data=f"quiz_answer:{answer_index}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Узнать об опеке ❤️",
                    callback_data="about_guardianship"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Связаться с сотрудником 📩",
                    callback_data="contact_zoo"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Оставить отзыв ⭐",
                    callback_data="leave_feedback"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Поделиться результатом 📤",
                    callback_data="share_result"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Пройти ещё раз 🔄",
                    callback_data="restart_quiz"
                )
            ]
        ]
    )


async def start_quiz_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(QuizState.answering)
    await state.update_data(
        question_index=0,
        scores={}
    )

    await callback.message.answer(
        QUESTIONS[0]["text"],
        reply_markup=question_keyboard(0)
    )


@router.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext) -> None:
    await start_quiz_flow(callback, state)
    await callback.answer()


@router.callback_query(F.data == "restart_quiz")
async def restart_quiz(callback: CallbackQuery, state: FSMContext) -> None:
    await start_quiz_flow(callback, state)
    await callback.answer()


@router.callback_query(QuizState.answering, F.data.startswith("quiz_answer:"))
async def process_answer(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    question_index = data["question_index"]
    scores = data["scores"]

    answer_index = int(callback.data.split(":")[1])
    answer = QUESTIONS[question_index]["answers"][answer_index]

    for animal, points in answer["scores"].items():
        scores[animal] = scores.get(animal, 0) + points

    await callback.message.edit_reply_markup(reply_markup=None)

    next_question_index = question_index + 1

    if next_question_index >= len(QUESTIONS):
        result_key = max(scores, key=scores.get)
        animal = ANIMALS[result_key]

        photo = FSInputFile(IMAGES_DIR / animal["image"])

        await callback.message.answer_photo(
            photo=photo,
            caption=f"{animal['description']}\n\n{animal['fact']}",
            reply_markup=result_keyboard()
        )

        await state.set_state(QuizState.finished)
        await state.update_data(
            result_key=result_key,
            result_name=animal["name"]
        )
    else:
        await state.update_data(
            question_index=next_question_index,
            scores=scores
        )

        await callback.message.answer(
            QUESTIONS[next_question_index]["text"],
            reply_markup=question_keyboard(next_question_index)
        )

    await callback.answer()

@router.callback_query(F.data == "about_guardianship")
async def about_guardianship(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "❤️ Программа «Возьми животное под опеку» помогает Московскому зоопарку "
        "заботиться о животных.\n\n"
        "Опекун вносит пожертвование на любую сумму, а средства идут на корм, "
        "уход и улучшение условий жизни обитателей зоопарка.\n\n"
        "Узнать больше можно на сайте Московского зоопарка:\n"
        "https://moscowzoo.ru/about/guardianship",
        reply_markup=back_to_result_keyboard()
    )

    await callback.answer()

@router.callback_query(F.data == "contact_zoo")
async def contact_zoo(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(QuizState.contact)

    await callback.message.answer(
        "📩 Напиши свой вопрос сотруднику зоопарка одним сообщением.\n\n"
        "Я передам его вместе с результатом твоей викторины."
    )

    await callback.answer()

@router.message(QuizState.contact)
async def process_contact_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    result_name = data.get("result_name", "результат не найден")

    username = f"@{message.from_user.username}" if message.from_user.username else "username не указан"

    admin_text = (
        "📩 Новый вопрос по программе опеки\n\n"
        f"Пользователь: {message.from_user.full_name}\n"
        f"Telegram: {username}\n"
        f"ID: {message.from_user.id}\n\n"
        f"Результат викторины: {result_name}\n\n"
        f"Вопрос:\n{message.text}"
    )

    await message.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text
    )

    await message.answer(
        "Спасибо! 🐾\n\n"
        "Твой вопрос и результат викторины переданы сотруднику зоопарка.\n"
        "Для демонстрации проекта сообщение отправляется администратору бота.",
        reply_markup=back_to_result_keyboard()
    )

    await state.set_state(QuizState.finished)

@router.callback_query(F.data == "leave_feedback")
async def leave_feedback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(QuizState.feedback)

    await callback.message.answer(
        "⭐ Напиши отзыв о викторине одним сообщением.\n\n"
        "Например: что понравилось, что было непонятно или что можно улучшить."
    )

    await callback.answer()

@router.message(QuizState.feedback)
async def process_feedback_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    result_name = data.get("result_name", "результат не найден")
    username = f"@{message.from_user.username}" if message.from_user.username else "username не указан"

    admin_text = (
        "⭐ Новый отзыв о викторине\n\n"
        f"Пользователь: {message.from_user.full_name}\n"
        f"Telegram: {username}\n"
        f"ID: {message.from_user.id}\n\n"
        f"Результат викторины: {result_name}\n\n"
        f"Отзыв:\n{message.text}"
    )

    await message.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text
    )

    await message.answer(
        "Спасибо за отзыв! 🐾\n\n"
        "Он поможет сделать викторину лучше.",
        reply_markup=back_to_result_keyboard()
    )

    await state.set_state(QuizState.finished)

@router.callback_query(F.data == "share_result")
async def share_result(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    result_name = data.get("result_name", "моё тотемное животное")

    share_text = (
        f"🐾 Я прошёл викторину Московского зоопарка!\n\n"
        f"Моё тотемное животное — {result_name}.\n\n"
        f"Пройди и ты: @zoo_ksks_bot"
    )

    await callback.message.answer(
        "📤 Скопируй этот текст и отправь друзьям:\n\n"
        f"{share_text}",
        reply_markup=back_to_result_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_result")
async def back_to_result(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)

    await show_result(callback, state)

    await callback.answer()

def back_to_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Вернуться к результату 🐾",
                    callback_data="back_to_result"
                )
            ]
        ]
    )

async def show_result(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    result_key = data.get("result_key")

    if not result_key:
        await callback.message.answer(
            "Результат не найден. Пройди викторину ещё раз.",
            reply_markup=result_keyboard()
        )
        return

    animal = ANIMALS[result_key]
    photo = FSInputFile(IMAGES_DIR / animal["image"])

    await callback.message.answer_photo(
        photo=photo,
        caption=f"{animal['description']}\n\n{animal['fact']}",
        reply_markup=result_keyboard()
    )
