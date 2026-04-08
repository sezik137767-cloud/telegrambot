import asyncio
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from openai import OpenAI

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ChatPermissions

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

router = Router()

TRIGGER_WORDS = [
    "заработок",
    "доход",
    "деньги",
    "в лс",
    "в личку",
    "пиши в лс",
    "пишите в лс",
    "без вложений",
    "скидка",
    "акция",
    "прибыль",
    "работа онлайн",
    "пассивный доход"
]


def has_trigger_words(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in TRIGGER_WORDS)


def check_advertising(text: str) -> str:
    response = client.chat.completions.create(
        model="openrouter/auto",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты модератор чата. "
                    "Определи, является ли сообщение рекламой. "
                    "Ответь строго одним словом: advertising или normal."
                )
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0,
        max_tokens=5
    )

    result = (response.choices[0].message.content or "").strip().lower()

    if "advertising" in result:
        return "advertising"

    return "normal"


async def mute_user_for_1_minute(message: Message):
    until_time = datetime.now(timezone.utc) + timedelta(minutes=1)

    await message.bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until_time
    )


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_message(message: Message):
    if not message.text:
        return

    if not has_trigger_words(message.text):
        return

    result = check_advertising(message.text)

    if result == "advertising":
        await message.reply(
    f"🚫 {message.from_user.full_name}, реклама найдена. Мут на 1 минуту."
)
        await mute_user_for_1_minute(message)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())