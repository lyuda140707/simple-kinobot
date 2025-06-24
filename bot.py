import os
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import asyncio
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎬 Фільми"), KeyboardButton(text="🎞 Серіали")],
    [KeyboardButton(text="✨ Мультики")]
], resize_keyboard=True)


async def get_films():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:html"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
            films = []
            rows = html.split("<tr")[2:]

            for row in rows:
                cols = row.split("<td")[1:]
                if len(cols) >= 3:
                    name = cols[0].split(">")[1].split("<")[0].strip()
                    link = cols[1].split(">")[1].split("<")[0].strip()
                    photo = cols[2].split(">")[1].split("<")[0].strip()
                    films.append({"name": name, "link": link, "photo": photo})
            return films


@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("🎬 Обери категорію або надішли назву фільму:", reply_markup=menu)


@dp.message()
async def universal_handler(message: Message):
    if message.video:
        file_id = message.video.file_id
        await message.reply(f"🎬 file_id цього відео:\n<code>{file_id}</code>")
        return

    if not message.text:
        return

    query = message.text.lower()
    films = await get_films()
    results = [f for f in films if query in f["name"].lower()]

    if not results:
        await message.answer("❗️ Нічого не знайдено")
        return

    for f in results:
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Дивитись", url=f["link"])]
        ]
    )

    await message.answer_photo(
        f["photo"],
        caption=f'🎬 {f["name"]}',
        reply_markup=buttons
    )


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
