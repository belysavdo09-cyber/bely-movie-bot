import os
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

# =========================
# SOZLAMALAR
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8251493317

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# DATABASE
# =========================

db = sqlite3.connect("movies.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    code TEXT PRIMARY KEY,
    file_id TEXT NOT NULL
)
""")

db.commit()

# Admin yuborgan oxirgi video
pending_video = {}


# =========================
# /start
# =========================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🎬 BELY MOVIE\n\n"
        "Kino kodini yuboring.\n"
        "Masalan: 101"
    )


# =========================
# ADMIN: VIDEO QABUL QILISH
# =========================

@dp.message(F.video)
async def receive_video(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    pending_video[ADMIN_ID] = message.video.file_id

    await message.answer(
        "✅ Video qabul qilindi!\n\n"
        "Endi ushbu kino uchun kod yuboring.\n"
        "Masalan: 101"
    )


# =========================
# ADMIN: KOD SAQLASH
# =========================

@dp.message(F.text)
async def receive_text(message: Message):

    user_id = message.from_user.id
    text = message.text.strip()

    # Admin video uchun kod yuborsa
    if user_id == ADMIN_ID and ADMIN_ID in pending_video:

        code = text

        cursor.execute(
            "INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)",
            (code, pending_video[ADMIN_ID])
        )

        db.commit()

        del pending_video[ADMIN_ID]

        await message.answer(
            f"✅ Kino muvaffaqiyatli saqlandi!\n\n"
            f"🎬 Kod: {code}"
        )

        return

    # =========================
    # KINO QIDIRISH
    # =========================

    cursor.execute(
        "SELECT file_id FROM movies WHERE code = ?",
        (text,)
    )

    result = cursor.fetchone()

    if result:
        file_id = result[0]

        await message.answer_video(
            video=file_id,
            caption="🎬 BELY MOVIE\n\n"
                    "🍿 Yoqimli tomosha!"
        )
    else:
        await message.answer(
            "❌ Bunday koddagi kino topilmadi."
        )


# =========================
# ADMIN: KINOLAR RO‘YXATI
# =========================

@dp.message(Command("list"))
async def list_movies(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT code FROM movies ORDER BY code")
    movies = cursor.fetchall()

    if not movies:
        await message.answer("📂 Hozircha kino yo‘q.")
        return

    text = "🎬 Saqlangan kinolar:\n\n"

    for movie in movies:
        text += f"🔹 {movie[0]}\n"

    await message.answer(text)


# =========================
# ADMIN: KINO O‘CHIRISH
# =========================

@dp.message(Command("delete"))
async def delete_movie(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            "❗ Foydalanish:\n"
            "/delete 101"
        )
        return

    code = parts[1].strip()

    cursor.execute(
        "DELETE FROM movies WHERE code = ?",
        (code,)
    )

    db.commit()

    if cursor.rowcount:
        await message.answer(
            f"🗑 Kino o‘chirildi: {code}"
        )
    else:
        await message.answer(
            "❌ Bunday kod topilmadi."
        )


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

async def main():
    print("BELY MOVIE BOT ISHLADI!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
