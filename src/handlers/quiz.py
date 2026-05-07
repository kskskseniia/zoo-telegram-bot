from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import FSInputFile

from src.data.questions import QUESTIONS
from src.states import QuizState
from src.data.animals import ANIMALS

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

        await state.clear()
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
        "https://moscowzoo.ru/about/guardianship"
    )

    await callback.answer()