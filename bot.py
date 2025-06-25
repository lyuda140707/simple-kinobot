import os
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import asyncio
from aiogram.client.default import DefaultBotProperties
from html import unescape

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
                if len(cols) >= 5:
                    category = unescape(cols[0].split(">")[1].split("<")[0]).replace("\xa0", "").strip()
                    name = cols[1].split(">")[1].split("<")[0].strip()
                    link = cols[2].split(">")[1].split("<")[0].strip()
                    photo = ""
                    if len(cols[3].split(">")) > 1:
                        photo = cols[3].split(">")[1].split("<")[0].strip()
                    photo = raw_photo if raw_photo else None
                    film_type = cols[4].split(">")[1].split("<")[0].strip()
                    films.append({
                        "category": category,
                        "name": name,
                        "link": link,
                        "photo": photo,
                        "type": film_type
                    })
            return films


@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("🎬 Обери категорію або напиши назву фільму чи серіалу:", reply_markup=menu)


@dp.message(Command("menu"))
async def menu_handler(message: Message):
    await message.answer("🔝 Головне меню:", reply_markup=menu)


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

    if message.text in ["🎬 Фільми", "🎞 Серіали", "✨ Мультики"]:
        selected_type = message.text
        results = [f for f in films if f["type"] == selected_type]

        if not results:
            await message.answer("❗️ Нічого не знайдено")
            return

        grouped = {}
        

        for cat, items in grouped.items():
            markup = InlineKeyboardMarkup(inline_keyboard=[])
            for i in items:
                btn = InlineKeyboardButton(text=i["name"], callback_data=f'play_{films.index(i)}')
                markup.inline_keyboard.append([btn])
            await message.answer(f'📂 {cat} — Обери серію або варіант:', reply_markup=markup)
        return

    results = [f for f in films if query in f["name"].lower() or query in f["category"].lower()]

    if not results:
        await message.answer("❗️ Нічого не знайдено")
        return

    grouped = {}
    for f in results:
        if not f["name"] or not f["category"]:
            continue
        grouped.setdefault(f["category"], []).append(f)

    for cat, items in grouped.items():
        markup = InlineKeyboardMarkup(inline_keyboard=[])
        for i in items:
            btn = InlineKeyboardButton(text=i["name"], callback_data=f'play_{films.index(i)}')
            markup.inline_keyboard.append([btn])
        title_text = cat if cat else "Результати пошуку"
        await message.answer(f'📂 {title_text} — Обери серію або варіант:', reply_markup=markup)


async def send_film(message: Message, film: dict):
    title = film["name"]
    category_text = f'{film["category"]} - ' if film["category"] else ""
    text = f'🎬 {category_text}{title}'

    if film["photo"]:
        await message.answer_photo(film["photo"], caption=text)
    else:

        await message.answer(text)
    if film["link"].startswith("http"):
        buttons = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="➡️ Дивитись", url=film["link"])]]
        )
        await message.answer("➡️ Натисни для перегляду:", reply_markup=buttons)
    elif film["link"]:  # навіть якщо немає фото, але є file_id відео
        await message.answer_video(film["link"], caption="🎬 Перегляд відео")
            
        




@dp.callback_query()
async def handle_buttons(call: types.CallbackQuery):
    await call.answer()
    films = await get_films()

    if not call.data.startswith("play_"):
        await call.message.answer("⚠️ Невідомий запит")
        return

    try:
        idx = int(call.data.replace("play_", ""))
        film = films[idx]
    except (ValueError, IndexError):
        await call.message.answer("⚠️ Помилка вибору")
        return

    title = film["name"]
    category_text = f'{film["category"]} - ' if film["category"] else ""
    text = f'🎬 {category_text}{title}'

    markup = InlineKeyboardMarkup(inline_keyboard=[])

    if film["category"]:
        same_series = [f for f in films if f["category"].strip().lower() == film["category"].strip().lower()]
        same_series_indices = [films.index(f) for f in same_series]
        current_pos = same_series_indices.index(idx)

        nav_buttons = []
        if current_pos > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Попередня", callback_data=f'play_{same_series_indices[current_pos - 1]}'))
        if current_pos < len(same_series) - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️ Наступна", callback_data=f'play_{same_series_indices[current_pos + 1]}'))

        if film["link"].startswith("http"):
            markup.inline_keyboard.append([InlineKeyboardButton(text="➡️ Дивитись", url=film["link"])])

        if nav_buttons:
            markup.inline_keyboard.append(nav_buttons)

    else:
        if film["link"].startswith("http"):
            markup.inline_keyboard.append([InlineKeyboardButton(text="➡️ Дивитись", url=film["link"])])

    if film["photo"]:
        await call.message.answer_photo(film["photo"], caption=text, reply_markup=markup)
    else:
        await call.message.answer(text, reply_markup=markup)
    if not film["link"].startswith("http") and film["link"]:
        await call.message.answer_video(film["link"], caption="🎬 Перегляд відео", reply_markup=markup)
       
    await call.message.answer("🏠 Повернутись у головне меню:", reply_markup=menu)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
