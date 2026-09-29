import os
import sqlite3
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8251493317

# =========================
# MAJBURIY TELEGRAM OBUNA
# =========================

TELEGRAM_CHANNELS = [
    ("@bely_movie", "https://t.me/bely_movie"),
    ("@bely_movie_chat", "https://t.me/bely_movie_chat"),
]

# Instagram
INSTAGRAM_LINK = "https://www.instagram.com/bely.movie/"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! Hostingda BOT_TOKEN ni sozlang.")

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

pending_video = {}

# =========================
# OBUNA TUGMALARI
# =========================

def subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 @bely_movie",
                    url="https://t.me/bely_movie"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 @bely_movie_chat",
                    url="https://t.me/bely_movie_chat"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📸 Instagram @bely.movie",
                    url=INSTAGRAM_LINK
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Obunani tekshirish",
                    callback_data="check_subscription"
                )
            ]
        ]
    )

# =========================
# OBUNANI TEKSHIRISH
# =========================

async def is_subscribed(user_id: int) -> bool:

    for channel, _ in TELEGRAM_CHANNELS:

        try:
            member = await bot.get_chat_member(
                channel,
                user_id
            )

            if member.status not in (
                "member",
                "administrator",
                "creator"
            ):
                return False

        except Exception as e:
            print(f"{channel} obuna tekshirish xatosi:", e)
            return False

    return True


async def require_subscription(message: Message) -> bool:

    if await is_subscribed(message.from_user.id):
        return True

    await message.answer(
        "🔒 BELY MOVIE botidan foydalanish uchun "
        "kanallarimizga obuna bo‘ling.\n\n"

        "1️⃣ @bely_movie kanaliga obuna bo‘ling\n"
        "2️⃣ @bely_movie_chat ga obuna bo‘ling\n"
        "3️⃣ Instagram sahifamizga o‘ting\n"
        "4️⃣ «Obunani tekshirish» tugmasini bosing",
        
        reply_markup=subscription_keyboard()
    )

    return False

# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    if not await require_subscription(message):
        return

    await message.answer(
        "🎬 BELY MOVIE\n\n"
        "Kino kodini yuboring.\n\n"
        "Masalan: 101"
    )

# =========================
# OBUNANI QAYTA TEKSHIRISH
# =========================

@dp.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery):

    if await is_subscribed(callback.from_user.id):

        await callback.message.edit_text(
            "✅ Obunalaringiz tasdiqlandi!\n\n"
            "🎬 Endi kino kodini yuboring.\n\n"
            "Masalan: 101"
        )

        await callback.answer()

    else:

        await callback.answer(
            "❌ Ikkala Telegram kanaliga ham obuna bo‘ling!",
            show_alert=True
        )

# =========================
# ADMIN VIDEO QABUL QILISH
# =========================

@dp.message(F.video)
async def receive_video(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    pending_video[ADMIN_ID] = message.video.file_id

    await message.answer(
        "✅ Video qabul qilindi!\n\n"
        "Endi kino kodini yuboring.\n\n"
        "Masalan: 101"
    )

# =========================
# KINOLAR RO‘YXATI
# =========================

@dp.message(Command("list"))
async def list_movies(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute(
        "SELECT code FROM movies ORDER BY code"
    )

    movies = cursor.fetchall()

    if not movies:
        await message.answer(
            "📂 Hozircha kino yo‘q."
        )
        return

    text = "🎬 Saqlangan kinolar:\n\n"

    for movie in movies:
        text += f"🔹 {movie[0]}\n"

    await message.answer(text)

# =========================
# KINO O‘CHIRISH
# =========================

@dp.message(Command("delete"))
async def delete_movie(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split(
        maxsplit=1
    )

    if len(parts) < 2:

        await message.answer(
            "❗ Foydalanish:\n\n"
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
# MATN / KINO KODI
# =========================

@dp.message(F.text)
async def receive_text(message: Message):

    user_id = message.from_user.id
    text = message.text.strip()

    # ADMIN KINO SAQLASH
    if (
        user_id == ADMIN_ID
        and ADMIN_ID in pending_video
    ):

        code = text

        cursor.execute(
            """
            INSERT OR REPLACE INTO movies
            (code, file_id)
            VALUES (?, ?)
            """,
            (
                code,
                pending_video[ADMIN_ID]
            )
        )

        db.commit()

        del pending_video[ADMIN_ID]

        await message.answer(
            f"✅ Kino muvaffaqiyatli saqlandi!\n\n"
            f"🎬 Kod: {code}"
        )

        return

    # MAJBURIY OBUNA
    if not await require_subscription(message):
        return

    # KINO QIDIRISH
    cursor.execute(
        "SELECT file_id FROM movies WHERE code = ?",
        (text,)
    )

    result = cursor.fetchone()

    if result:

        await message.answer_video(
            video=result[0],
            caption=(
                "🎬 BELY MOVIE\n\n"
                "🍿 Yoqimli tomosha!"
            )
        )

    else:

        await message.answer(
            "❌ Bunday koddagi kino topilmadi."
        )

# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

async def main():

    print("BELY MOVIE BOT ISHLADI!")

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
