from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# ═══════════════════════════════════════════════
#          FOYDALANUVCHI TUGMALARI
# ═══════════════════════════════════════════════

def subscription_kb(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        # Majburiy obunaga faqat Telegram kanallar kiradi
        if ch['platform'] == 'telegram':
            buttons.append([InlineKeyboardButton(text=f"📢 {ch['title']}", url=ch['link'])])
    buttons.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def user_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔍 Kino qidirish")]],
        resize_keyboard=True
    )

def user_movie_types_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Pullik kinolar", callback_data="search_pullik"),
            InlineKeyboardButton(text="🆓 Tekin kinolar", callback_data="search_tekin")
        ]
    ])

def user_cancel_search_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Qaytish", callback_data="cancel_search")]
    ])

def yana_kino_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yana kino qidirish", callback_data="ask_new_code")]
    ])

def rating_kb() -> InlineKeyboardMarkup:
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
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kino bo'limi"), KeyboardButton(text="📢 Kanal bo'limi")],
            [KeyboardButton(text="📊 Oylik statistika"), KeyboardButton(text="📣 Reklama")],
            [KeyboardButton(text="⭐ Reyting so'rash")]
        ],
        resize_keyboard=True
    )

def admin_movie_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kino qo'shish"), KeyboardButton(text="🗑 Kino o'chirish")],
            [KeyboardButton(text="📋 Bor kinolar ro'yxati")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

def admin_movie_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Pullik", callback_data="type_pullik"),
            InlineKeyboardButton(text="🆓 Tekin", callback_data="type_tekin")
        ]
    ])

def admin_channel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kanal qo'shish"), KeyboardButton(text="🗑 Kanal o'chirish")],
            [KeyboardButton(text="📋 Bor kanallar ro'yxati")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

def admin_platform_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔹 Telegram", callback_data="plat_telegram"),
            InlineKeyboardButton(text="🔸 Instagram", callback_data="plat_instagram"),
            InlineKeyboardButton(text="🔻 YouTube", callback_data="plat_youtube")
        ]
    ])

def admin_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )