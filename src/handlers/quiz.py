from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from src.data.questions import QUESTIONS

router = Router()


def question_keyboard(question_index: int) -> InlineKeyboardMarkup:
    buttons = []

    for answer_index, answer in enumerate(QUESTIONS[question_index]["answers"]):
        buttons.append([
            InlineKeyboardButton(
                text=answer["text"],
                callback_data=f"quiz_answer:{question_index}:{answer_index}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery) -> None:
    await callback.message.answer(
        QUESTIONS[0]["text"],
        reply_markup=question_keyboard(0)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("quiz_answer:"))
async def process_answer(callback: CallbackQuery) -> None:
    data = callback.data.split(":")
    question_index = int(data[1])
    answer_index = int(data[2])

    next_question_index = question_index + 1
    await callback.message.edit_reply_markup(reply_markup=None)

    if next_question_index >= len(QUESTIONS):
        await callback.message.answer(
            "Викторина завершена! 🐾\n\n"
            "Скоро здесь будет результат."
        )
    else:
        await callback.message.answer(
            QUESTIONS[next_question_index]["text"],
            reply_markup=question_keyboard(next_question_index)
        )

    await callback.answer()