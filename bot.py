import os
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
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

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.reply("🎬 Привіт! Надішли мені назву фільму для пошуку:")

@dp.message_handler()
async def search(msg: types.Message):
    query = msg.text.lower()
    films = await get_films()
    results = [f for f in films if query in f["name"].lower()]

    if not results:
        await msg.reply("❗️ Нічого не знайдено")
        return

    for f in results:
        await msg.reply_photo(f["photo"], caption=f'🎬 {f["name"]}\n➡️ [Дивитись]({f["link"]})', parse_mode="Markdown")

if __name__ == "__main__":
    executor.start_polling(dp)
