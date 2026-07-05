import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID
import database as db
from button import (
    subscription_kb, yana_kino_kb, rating_kb, user_main_kb,
    admin_main_kb, admin_movie_kb, admin_channel_kb, admin_cancel_kb
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())


# ═══════════════════════════════════════════════
#                HOLATLAR (FSM)
# ═══════════════════════════════════════════════

class UserState(StatesGroup):
    waiting_code   = State()   # kino kodini kutish
    waiting_error  = State()   # /xatolik xabarini kutish


class AdminState(StatesGroup):
    # Kino qo'shish
    movie_video   = State()
    movie_code    = State()
    movie_title   = State()
    # Kino o'chirish
    delete_code   = State()
    # Reklama
    advert        = State()
    # Kanal qo'shish
    ch_id         = State()
    ch_title      = State()
    ch_link       = State()
    # Kanal o'chirish
    ch_remove     = State()


# ═══════════════════════════════════════════════
#               YORDAMCHI FUNKSIYALAR
# ═══════════════════════════════════════════════

async def is_subscribed(user_id: int) -> bool:
    """Foydalanuvchi barcha faol kanallarga a'zoligini tekshirish"""
    channels = db.get_active_channels()
    if not channels:
        return True

    for ch in channels:
        ch_id = str(ch["channel_id"]).strip()

        if "t.me/" in ch_id:
            ch_id = "@" + ch_id.split("t.me/")[1].split("/")[0]
        elif not ch_id.startswith("@") and not ch_id.startswith("-100") and not ch_id.isdigit():
            ch_id = "@" + ch_id

        try:
            member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                logger.warning(f"Foydalanuvchi {user_id} unga obuna emas: {ch_id}")
                return False
        except Exception as e:
            logger.error(f"Kanalni tekshirishda xatolik ({ch_id}): {e}")
            return False
    return True


async def prompt_code(target) -> None:
    """Kino kodini so'rash xabarini yuborish (Message yoki CallbackQuery.message uchun)"""
    await target.answer(
        "🔢 <b>Kino kodini kiriting:</b>\n\n<i>Masalan: 1234</i>",
        parse_mode="HTML",
        reply_markup=user_main_kb()
    )


# ═══════════════════════════════════════════════
#         FOYDALANUVCHI — /start
# ═══════════════════════════════════════════════

@dp.message(CommandStart(), F.from_user.id != ADMIN_ID)
async def user_start(message: Message, state: FSMContext):
    db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    channels = db.get_active_channels()

    if channels and not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>",
            reply_markup=subscription_kb(channels),
            parse_mode="HTML"
        )
    else:
        await state.set_state(UserState.waiting_code)
        await message.answer(
            "🎬 <b>Kino Botga xush kelibsiz!</b>",
            parse_mode="HTML"
        )
        await prompt_code(message)


# ── Obuna tekshirish callback ────────────────────────────

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(call: CallbackQuery, state: FSMContext):
    if await is_subscribed(call.from_user.id):
        await state.set_state(UserState.waiting_code)
        await call.message.edit_text(
            "✅ <b>Obuna tasdiqlandi!</b>",
            parse_mode="HTML"
        )
        await prompt_code(call.message)
    else:
        await call.answer("❌ Siz hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True)


# ── Kino olingandan keyin — yana kino kodi kiritish ──────

@dp.callback_query(F.data == "ask_new_code")
async def ask_new_code(call: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_code)
    await prompt_code(call.message)
    await call.answer()


# ═══════════════════════════════════════════════
#         FOYDALANUVCHI — KOD ORQALI KINO
# ═══════════════════════════════════════════════

@dp.message(F.text == "🔍 Kino qidirish", F.from_user.id != ADMIN_ID)
async def user_search_button(message: Message, state: FSMContext):
    channels = db.get_active_channels()
    if channels and not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>",
            reply_markup=subscription_kb(channels),
            parse_mode="HTML"
        )
        return

    await state.set_state(UserState.waiting_code)
    await prompt_code(message)


@dp.message(UserState.waiting_code, F.from_user.id != ADMIN_ID)
async def send_movie(message: Message, state: FSMContext):
    code = message.text.strip()
    movie = db.get_movie_by_code(code)
    if not movie:
        await message.answer(
            "❌ <b>Bunday kodli kino topilmadi.</b>\nKodni tekshirib, qaytadan urinib ko'ring.",
            parse_mode="HTML"
        )
        return

    await state.clear()
    await message.answer_video(
        video=movie["file_id"],
        caption=f"🎬 <b>{movie['title']}</b>",
        parse_mode="HTML",
        reply_markup=yana_kino_kb()
    )


# ═══════════════════════════════════════════════
#         FOYDALANUVCHI — /about va /xatolik
# ═══════════════════════════════════════════════

@dp.message(Command("about"))
async def about_cmd(message: Message):
    await message.answer(
        "ℹ️ <b>Bot haqida</b>\n\n"
        "🎬 Bu bot orqali siz kino kodini kiritib, istalgan kinoni tez va oson tomosha qilishingiz mumkin.\n\n"
        "Har doim yangi kinolar qo'shib boriladi! 🍿\n\n"
        "Savol yoki muammo bo'lsa — /xatolik buyrug'idan foydalaning.",
        parse_mode="HTML"
    )


@dp.message(Command("xatolik"), F.from_user.id != ADMIN_ID)
async def report_error_start(message: Message, state: FSMContext):
    await state.set_state(UserState.waiting_error)
    await message.answer(
        "✍️ <b>Xatolik haqida xabaringizni yozing:</b>\n\n"
        "<i>Xabaringiz to'g'ridan-to'g'ri adminga yuboriladi, botdan chiqmasangiz ham bo'ladi.</i>",
        parse_mode="HTML"
    )


@dp.message(UserState.waiting_error, F.from_user.id != ADMIN_ID)
async def report_error_finish(message: Message, state: FSMContext):
    await state.clear()

    if not message.text:
        await message.answer("⚠️ Iltimos, xatolikni matn ko'rinishida yozing.")
        await state.set_state(UserState.waiting_error)
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else "yo'q"
    try:
        await bot.send_message(
            ADMIN_ID,
            f"⚠️ <b>Yangi xatolik xabari</b>\n\n"
            f"👤 Ism: {user.full_name}\n"
            f"🔗 Username: {username}\n"
            f"🆔 ID: <code>{user.id}</code>\n\n"
            f"📝 <b>Xabar:</b>\n{message.text}",
            parse_mode="HTML"
        )
        await message.answer("✅ Xabaringiz adminga yuborildi. Tez orada javob beriladi!")
    except Exception as e:
        logger.error(f"Xatolik xabarini yuborishda muammo: {e}")
        await message.answer("❌ Xabar yuborishda xatolik yuz berdi. Keyinroq urinib ko'ring.")

    await state.set_state(UserState.waiting_code)
    await prompt_code(message)


# ── Foydalanuvchi bahosi (1-5 yulduz) ────────────────────

@dp.callback_query(F.data.startswith("rate_"))
async def rating_callback(call: CallbackQuery):
    rating = int(call.data.split("_")[1])
    db.add_rating(call.from_user.id, rating)
    await call.message.edit_text(
        f"🙏 <b>Rahmat!</b> Siz botni {rating}⭐ deb baholadingiz.",
        parse_mode="HTML"
    )
    await call.answer()


# ═══════════════════════════════════════════════
#                  ADMIN — /start
# ═══════════════════════════════════════════════

@dp.message(CommandStart(), F.from_user.id == ADMIN_ID)
async def admin_start(message: Message, state: FSMContext):
    await state.clear()
    name = message.from_user.username or message.from_user.first_name
    await message.answer(
        f"👋 Assalomu alaykum <b>@{name}</b>!\n\nSizga nima yordam bera olaman? 😊",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════
#            ADMIN — BO'LIM NAVIGATSIYASI
# ═══════════════════════════════════════════════

@dp.message(F.text == "🎬 Kino bo'limi", F.from_user.id == ADMIN_ID)
async def admin_movie_section(message: Message):
    await message.answer(
        "🎬 <b>Kino bo'limi</b>\n\nKerakli amalni tanlang 👇",
        reply_markup=admin_movie_kb(),
        parse_mode="HTML"
    )


@dp.message(F.text == "📢 Kanal bo'limi", F.from_user.id == ADMIN_ID)
async def admin_channel_section(message: Message):
    await message.answer(
        "📢 <b>Kanal bo'limi</b>\n\nKerakli amalni tanlang 👇",
        reply_markup=admin_channel_kb(),
        parse_mode="HTML"
    )


@dp.message(F.text == "⬅️ Orqaga", F.from_user.id == ADMIN_ID)
async def admin_back_to_main(message: Message):
    await message.answer(
        "🏠 <b>Asosiy menyu</b>",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════
#            ADMIN — OYLIK STATISTIKA
# ═══════════════════════════════════════════════

@dp.message(F.text == "📊 Oylik statistika", F.from_user.id == ADMIN_ID)
async def admin_stats(message: Message):
    stats = db.get_monthly_stats()
    total = db.get_total_users()
    rating = db.get_monthly_rating()
    await message.answer(
        f"📊 <b>Oylik statistika ({stats['month']})</b>\n\n"
        f"➕ Qo'shilganlar: <b>{stats['joined']}</b>\n"
        f"➖ Chiqib ketganlar: <b>{stats['left']}</b>\n"
        f"👥 Jami aktiv: <b>{total}</b>\n"
        f"⭐ O'rtacha baho: <b>{rating['avg']}</b> ({rating['count']} ta baho)",
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════
#                ADMIN — REKLAMA
# ═══════════════════════════════════════════════

@dp.message(F.text == "📣 Reklama", F.from_user.id == ADMIN_ID)
async def admin_advert_ask(message: Message, state: FSMContext):
    await state.set_state(AdminState.advert)
    await message.answer(
        "📢 <b>Reklama xabarini yuboring:</b>\n"
        "<i>(Matn, rasm, video — istalgan format)</i>",
        reply_markup=admin_cancel_kb(),
        parse_mode="HTML"
    )


@dp.message(AdminState.advert, F.from_user.id == ADMIN_ID)
async def admin_advert_send(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return

    await state.clear()
    users = db.get_all_user_ids()
    ok = 0
    fail = 0
    progress = await message.answer(f"⏳ Yuborilmoqda: 0/{len(users)}")

    for i, uid in enumerate(users, 1):
        try:
            await message.copy_to(uid)
            ok += 1
        except Exception:
            fail += 1
        if i % 30 == 0:
            try:
                await progress.edit_text(f"⏳ Yuborilmoqda: {i}/{len(users)}")
            except Exception:
                pass

    await progress.edit_text(
        f"✅ <b>Reklama yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {ok}\n"
        f"❌ Yuborilmadi: {fail}",
        parse_mode="HTML"
    )
    await message.answer("Bosh sahifa 👇", reply_markup=admin_main_kb())


# ═══════════════════════════════════════════════
#            ADMIN — REYTING SO'RASH
# ═══════════════════════════════════════════════

@dp.message(F.text == "⭐ Reyting so'rash", F.from_user.id == ADMIN_ID)
async def admin_request_rating(message: Message):
    users = db.get_all_user_ids()
    ok = 0
    fail = 0
    progress = await message.answer(f"⏳ Yuborilmoqda: 0/{len(users)}")

    for i, uid in enumerate(users, 1):
        try:
            await bot.send_message(
                uid,
                "🙏 <b>Botimizni baholab keting!</b>\n\nSizga bot qanchalik yoqdi? 1 dan 5 gacha yulduz tanlang 👇",
                reply_markup=rating_kb(),
                parse_mode="HTML"
            )
            ok += 1
        except Exception:
            fail += 1
        if i % 30 == 0:
            try:
                await progress.edit_text(f"⏳ Yuborilmoqda: {i}/{len(users)}")
            except Exception:
                pass

    await progress.edit_text(
        f"✅ <b>Reyting so'rovi yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {ok}\n"
        f"❌ Yuborilmadi: {fail}",
        parse_mode="HTML"
    )
    await message.answer("Bosh sahifa 👇", reply_markup=admin_main_kb())


# ═══════════════════════════════════════════════
#            ADMIN — KINO QO'SHISH ZANJIRI
# ═══════════════════════════════════════════════

@dp.message(F.text == "➕ Kino qo'shish", F.from_user.id == ADMIN_ID)
async def admin_movie_add_step1(message: Message, state: FSMContext):
    await state.set_state(AdminState.movie_video)
    await message.answer(
        "🎬 <b>Kino faylini (yoki videoni) yuboring:</b>\n\n"
        "<i>Eslatma: Kinoni video formatida yoki Hujjat (Document) ko'rinishida yuborishingiz mumkin.</i>",
        reply_markup=admin_cancel_kb(),
        parse_mode="HTML"
    )


@dp.message(AdminState.movie_video, F.from_user.id == ADMIN_ID)
async def admin_movie_add_step2(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_movie_kb())
        return

    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    else:
        await message.answer("⚠️ Iltimos, faqat kino faylini (video yoki dokument) yuboring!")
        return

    await state.update_data(file_id=file_id)
    await state.set_state(AdminState.movie_code)
    await message.answer(
        "🔢 <b>Kino uchun kod kiriting:</b>\n\n<i>Masalan: 552</i>",
        parse_mode="HTML"
    )


@dp.message(AdminState.movie_code, F.from_user.id == ADMIN_ID)
async def admin_movie_add_step3(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_movie_kb())
        return

    code = message.text.strip()

    if db.get_movie_by_code(code):
        await message.answer(
            f"❌ <b>{code}</b> kodi band! Iltimos, boshqa kod kiriting:",
            parse_mode="HTML"
        )
        return

    await state.update_data(code=code)
    await state.set_state(AdminState.movie_title)
    await message.answer(
        "✏️ <b>Kino nomini (sarlavhasini) kiriting:</b>",
        parse_mode="HTML"
    )


@dp.message(AdminState.movie_title, F.from_user.id == ADMIN_ID)
async def admin_movie_add_finish(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_movie_kb())
        return

    title = message.text.strip()
    data = await state.get_data()
    await state.clear()

    ok = db.add_movie(data["code"], title, data["file_id"], "tekin")
    if ok:
        await message.answer(
            f"✅ <b>Kino muvaffaqiyatli qo'shildi!</b>\n\n"
            f"🎬 Nomi: <b>{title}</b>\n"
            f"🔢 Kodi: <code>{data['code']}</code>",
            reply_markup=admin_movie_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Bazaga saqlashda xatolik yuz berdi!",
            reply_markup=admin_movie_kb()
        )


# ═══════════════════════════════════════════════
#            ADMIN — KINOLAR RO'YXATI
# ═══════════════════════════════════════════════

@dp.message(F.text == "📋 Kinolar ro'yxati", F.from_user.id == ADMIN_ID)
async def admin_movie_list(message: Message):
    movies = db.get_all_movies()
    if not movies:
        await message.answer("📭 Hozircha hech qanday kino yo'q.")
        return

    text = f"🎞 <b>Mavjud kinolar ({len(movies)} ta):</b>\n\n"
    for m in movies:
        type_icon = "💰" if m.get("movie_type") == "pullik" else "🆓"
        text += f"{type_icon} <b>{m['title']}</b>  —  <code>{m['code']}</code>\n"

    # Telegram xabar chegarasi (4096) dan uzun bo'lsa qismlarga bo'lib yuboramiz
    if len(text) <= 4096:
        await message.answer(text, parse_mode="HTML")
    else:
        for i in range(0, len(text), 4096):
            await message.answer(text[i:i + 4096], parse_mode="HTML")


# ═══════════════════════════════════════════════
#            ADMIN — KINO O'CHIRISH
# ═══════════════════════════════════════════════

@dp.message(F.text == "🗑 Kino o'chirish", F.from_user.id == ADMIN_ID)
async def admin_movie_del_ask(message: Message, state: FSMContext):
    movies = db.get_all_movies()
    if not movies:
        await message.answer("📭 Hozircha hech qanday kino yo'q.")
        return

    text = "🎞 <b>Mavjud kinolar:</b>\n\n"
    for m in movies:
        text += f"• {m['title']}  —  <code>{m['code']}</code>\n"
    text += "\n🗑 O'chirmoqchi bo'lgan kino kodini yuboring:"

    await state.set_state(AdminState.delete_code)
    await message.answer(text, reply_markup=admin_cancel_kb(), parse_mode="HTML")


@dp.message(AdminState.delete_code, F.from_user.id == ADMIN_ID)
async def admin_movie_del_finish(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_movie_kb())
        return
    await state.clear()
    ok = db.delete_movie(message.text.strip())
    if ok:
        await message.answer("✅ Kino o'chirildi!", reply_markup=admin_movie_kb())
    else:
        await message.answer("❌ Bunday kodli kino topilmadi!", reply_markup=admin_movie_kb())


# ═══════════════════════════════════════════════
#            ADMIN — KANAL QO'SHISH ZANJIRI
# ═══════════════════════════════════════════════

@dp.message(F.text == "➕ Kanal qo'shish", F.from_user.id == ADMIN_ID)
async def admin_ch_add_step1(message: Message, state: FSMContext):
    await state.set_state(AdminState.ch_id)
    await message.answer(
        "➕ <b>Kanal ID'sini yoki Username'ini kiriting:</b>\n\n"
        "<i>Masalan: -100123456789 yoki @kanal_username</i>\n\n"
        "⚠️ <b>Muhim:</b> Bot ushbu kanalda admin bo'lishi shart!",
        reply_markup=admin_cancel_kb(),
        parse_mode="HTML"
    )


@dp.message(AdminState.ch_id, F.from_user.id == ADMIN_ID)
async def admin_ch_add_step2(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_channel_kb())
        return

    await state.update_data(ch_id=message.text.strip())
    await state.set_state(AdminState.ch_title)
    await message.answer("✏️ <b>Kanal nomini kiriting:</b>\n<i>(Masalan: Premyera Kinolar)</i>", parse_mode="HTML")


@dp.message(AdminState.ch_title, F.from_user.id == ADMIN_ID)
async def admin_ch_add_step3(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_channel_kb())
        return

    await state.update_data(ch_title=message.text.strip())
    await state.set_state(AdminState.ch_link)
    await message.answer("🔗 <b>Kanal uchun havola (link) kiriting:</b>\n<i>(Masalan: https://t.me/kanal_username)</i>", parse_mode="HTML")


@dp.message(AdminState.ch_link, F.from_user.id == ADMIN_ID)
async def admin_ch_add_finish(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_channel_kb())
        return

    link = message.text.strip()
    data = await state.get_data()
    await state.clear()

    ok = db.add_channel(data["ch_id"], data["ch_title"], link, "telegram")
    if ok:
        await message.answer(
            f"✅ <b>Kanal majburiy obunaga muvaffaqiyatli qo'shildi!</b>\n\n"
            f"📢 Nomi: <b>{data['ch_title']}</b>\n"
            f"🆔 ID: <code>{data['ch_id']}</code>\n"
            f"🔗 Link: {link}",
            reply_markup=admin_channel_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Kanalni bazaga saqlashda xatolik yuz berdi!", reply_markup=admin_channel_kb())


# ═══════════════════════════════════════════════
#            ADMIN — KANALLAR RO'YXATI
# ═══════════════════════════════════════════════

@dp.message(F.text == "📋 Kanallar ro'yxati", F.from_user.id == ADMIN_ID)
async def admin_channel_list(message: Message):
    channels = db.get_active_channels()
    if not channels:
        await message.answer("📭 Hozircha hech qanday kanal yo'q.")
        return

    text = f"📋 <b>Faol kanallar ({len(channels)} ta):</b>\n\n"
    for ch in channels:
        platform_icon = "📢" if ch.get("platform") == "telegram" else "🌐"
        text += (
            f"{platform_icon} <b>{ch['title']}</b>\n"
            f"   🆔 ID: <code>{ch['channel_id']}</code>\n"
            f"   🔗 Link: {ch['link']}\n\n"
        )

    if len(text) <= 4096:
        await message.answer(text, parse_mode="HTML")
    else:
        for i in range(0, len(text), 4096):
            await message.answer(text[i:i + 4096], parse_mode="HTML")


# ═══════════════════════════════════════════════
#            ADMIN — KANAL O'CHIRISH
# ═══════════════════════════════════════════════

@dp.message(F.text == "➖ Kanal o'chirish", F.from_user.id == ADMIN_ID)
async def admin_ch_remove_ask(message: Message, state: FSMContext):
    channels = db.get_active_channels()
    if not channels:
        await message.answer("📭 Hozircha hech qanday kanal yo'q.")
        return

    text = "📋 <b>Faol kanallar:</b>\n\n"
    for ch in channels:
        text += f"• {ch['title']}  —  <code>{ch['channel_id']}</code>\n"
    text += "\n✏️ O'chirmoqchi bo'lgan kanal username'ini yuboring:"

    await state.set_state(AdminState.ch_remove)
    await message.answer(text, reply_markup=admin_cancel_kb(), parse_mode="HTML")


@dp.message(AdminState.ch_remove, F.from_user.id == ADMIN_ID)
async def admin_ch_remove_finish(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_channel_kb())
        return
    await state.clear()
    ok = db.remove_channel(message.text.strip())
    if ok:
        await message.answer("✅ Kanal majburiy obunadan olib tashlandi!", reply_markup=admin_channel_kb())
    else:
        await message.answer("❌ Bunday kanal topilmadi!", reply_markup=admin_channel_kb())


# ═══════════════════════════════════════════════
#                BOTNI ISHGA TUSHIRISH
# ═══════════════════════════════════════════════

async def set_commands():
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni qayta ishga tushurish"),
        BotCommand(command="about", description="Bot haqida"),
        BotCommand(command="xatolik", description="Xatolik haqida adminga xabar berish"),
    ])


async def main():
    db.init_db()
    await set_commands()
    logger.info("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
