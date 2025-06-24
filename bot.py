import os
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
import asyncio
from aiogram.client.default import DefaultBotProperties

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)


async def get_films():
    async with aiohttp.ClientSession() as session:
        async with session.get(SPREADSHEET_URL) as resp:
            html = await resp.text()
            films = []
            rows = html.split("<tr")[2:]  # Пропускаємо заголовок

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
    await message.answer("🎬 Привіт! Надішли мені назву фільму для пошуку:")


@dp.message()
async def search_handler(message: Message):
    query = message.text.lower()
    films = await get_films()
    results = [f for f in films if query in f["name"].lower()]

    if not results:
        await message.answer("❗️ Нічого не знайдено")
        return

    for f in results:
        await message.answer_photo(
            f["photo"],
            caption=f'🎬 {f["name"]}\n➡️ <a href="{f["link"]}">Дивитись</a>'
        )


@dp.message(lambda message: message.video is not None)
async def get_file_id(msg: types.Message):
    file_id = msg.video.file_id
    await msg.reply(f"🎬 file_id цього відео:\n<code>{file_id}</code>")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
