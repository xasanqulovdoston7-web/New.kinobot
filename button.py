from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)


# ═══════════════════════════════════════════════
#          FOYDALANUVCHI TUGMALARI
# ═══════════════════════════════════════════════

def subscription_kb(channels: list) -> InlineKeyboardMarkup:
    """Majburiy obuna — kanallar + tekshirish tugmasi"""
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ch['title']}",
            url=ch['link']
        )])
    buttons.append([InlineKeyboardButton(
        text="✅ Obunani tekshirish",
        callback_data="check_sub"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_main_kb() -> ReplyKeyboardMarkup:
    """Foydalanuvchi — doimiy asosiy klaviatura"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Kino qidirish")],
        ],
        resize_keyboard=True
    )


def user_main_kb() -> ReplyKeyboardMarkup:
    """Foydalanuvchi — doimiy asosiy klaviatura (har doim ko'rinib turadi)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Kino qidirish")],
        ],
        resize_keyboard=True
    )


def yana_kino_kb() -> InlineKeyboardMarkup:
    """Kino yuborilgandan keyin chiqadigan — yana kino kodi kiritish tugmasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yana kino olish", callback_data="ask_new_code")]
    ])


def rating_kb() -> InlineKeyboardMarkup:
    """Botni 1-5 yulduz bilan baholash"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1⭐", callback_data="rate_1"),
            InlineKeyboardButton(text="2⭐", callback_data="rate_2"),
            InlineKeyboardButton(text="3⭐", callback_data="rate_3"),
            InlineKeyboardButton(text="4⭐", callback_data="rate_4"),
            InlineKeyboardButton(text="5⭐", callback_data="rate_5"),
        ]
    ])


# ═══════════════════════════════════════════════
#          ADMIN TUGMALARI
# ═══════════════════════════════════════════════

def admin_main_kb() -> ReplyKeyboardMarkup:
    """Admin — asosiy bo'limlar menyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎬 Kino bo'limi"),
                KeyboardButton(text="📢 Kanal bo'limi"),
            ],
            [
                KeyboardButton(text="📊 Oylik statistika"),
                KeyboardButton(text="📣 Reklama"),
            ],
            [
                KeyboardButton(text="⭐ Reyting so'rash"),
            ],
        ],
        resize_keyboard=True
    )


def admin_movie_kb() -> ReplyKeyboardMarkup:
    """Admin — Kino bo'limi submenyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Kino qo'shish"),
                KeyboardButton(text="🗑 Kino o'chirish"),
            ],
            [
                KeyboardButton(text="📋 Kinolar ro'yxati"),
            ],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True
    )


def admin_channel_kb() -> ReplyKeyboardMarkup:
    """Admin — Kanal bo'limi submenyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Kanal qo'shish"),
                KeyboardButton(text="➖ Kanal o'chirish"),
            ],
            [
                KeyboardButton(text="📋 Kanallar ro'yxati"),
            ],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True
    )


def admin_cancel_kb() -> ReplyKeyboardMarkup:
    """Admin — jarayon bekor qilish"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
