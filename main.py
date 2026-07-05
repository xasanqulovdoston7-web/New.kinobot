import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID, ADMIN_USERNAME
import database as db
from button import (
    subscription_kb, user_main_kb, user_movie_types_kb, user_cancel_search_kb, yana_kino_kb, rating_kb,
    admin_main_kb, admin_movie_kb, admin_movie_type_kb, admin_channel_kb, admin_platform_kb, admin_cancel_kb
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ═══════════════════════════════════════════════
#                HOLATLAR (FSM)
# ═══════════════════════════════════════════════

class UserState(StatesGroup):
    waiting_code  = State()   # kino kodini kutish
    waiting_error = State()   # /xatolik xabarini kutish

class AdminState(StatesGroup):
    # Kino qo'shish
    movie_type    = State()
    movie_video   = State()
    movie_code    = State()
    movie_title   = State()
    # Kino o'chirish
    delete_code   = State()
    # Reklama
    advert        = State()
    # Kanal qo'shish
    ch_platform   = State()
    ch_id         = State()
    ch_title      = State()
    ch_link       = State()
    ch_subs       = State()
    # Kanal o'chirish
    ch_remove     = State()

# ═══════════════════════════════════════════════
#               YORDAMCHI FUNKSIYALAR
# ═══════════════════════════════════════════════

async def is_subscribed(user_id: int) -> bool:
    channels = db.get_active_channels()
    if not channels:
        return True

    for ch in channels:
        if ch['platform'] != 'telegram':
            continue  # Instagram/YouTube tekshirib bo'lmaydi, o'tkazib yuboramiz
        
        ch_id = str(ch["channel_id"]).strip()
        if "t.me/" in ch_id:
            ch_id = "@" + ch_id.split("t.me/")[1].split("/")[0]
        elif not ch_id.startswith("@") and not ch_id.startswith("-100") and not ch_id.isdigit():
            ch_id = "@" + ch_id

        try:
            member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception as e:
            logger.error(f"Kanalni tekshirishda xatolik ({ch_id}): {e}")
            return False
    return True

# ═══════════════════════════════════════════════
#             FOYDALANUVCHI HANDLERLARI
# ═══════════════════════════════════════════════

from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardRemove

# 1. BOSH MENYUDAN KINO QIDIRISH BOSILGANDA (Faqat holatsiz paytda ishlaydi)
@dp.message(F.text == "🔍 Kino qidirish", F.from_user.id != ADMIN_ID, StateFilter(None))
async def user_search_movie(message: Message):
    await message.answer(
        "Kino turini tanlang 👇",
        reply_markup=user_movie_types_kb()
    )

# 2. INLINE TUGMADAN KINO TURI TANLANGANDA (Kodni so'rash va Reply Keyboard'ni yashirish)
@dp.callback_query(F.data.startswith("search_"))
async def user_search_type_selected(call: CallbackQuery, state: FSMContext):
    m_type = call.data.split("_")[1]
    await state.update_data(search_type=m_type)
    await state.set_state(UserState.waiting_code)
    
    # Reply keyboard (Kino qidirish) tugmasini butunlay yashiramiz
    remove_msg = await call.message.answer("⌨️ Qidiruv rejimi ishga tushdi.", reply_markup=ReplyKeyboardRemove())
    await remove_msg.delete() # Bu xabar ko'rinib qolmasligi uchun o'sha zahoti o'chiriladi
    
    await call.message.edit_text(
        f"🔢 <b>[{m_type.upper()}] Kino kodini kiriting:</b>\n\n<i>Masalan: 123</i>",
        reply_markup=user_cancel_search_kb(),
        parse_mode="HTML"
    )

# 3. FAQAT INLINE "⬅️ QAYTISH" TUGMASI BOSILGANDA BOSH MENYU TUGMASINI QAYTARISH
@dp.callback_query(F.data == "cancel_search", UserState.waiting_code)
async def cancel_search_callback(call: CallbackQuery, state: FSMContext):
    await state.clear() # FSM holatidan butunlay chiqamiz
    await call.message.delete()
    # Foydalanuvchiga bosh menyu reply tugmasini qaytarib beramiz
    await call.message.answer("Bosh menyuga qaytdingiz.", reply_markup=user_main_kb())

# 4. YANA KINO QIDIRISH (INLINE TUGMA) BOSILGANDA
@dp.callback_query(F.data == "ask_new_code")
async def ask_new_code(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    # Qayta so'rashda ham reply keyboard yashirin holatda qolishi uchun holatni tekshiramiz
    await call.message.answer("Kino turini tanlang 👇", reply_markup=user_movie_types_kb())

# 5. KOD KIRITILGANDA KINONI QIDIRIB TOPISH VA JAVOB BERISH
@dp.message(UserState.waiting_code, F.from_user.id != ADMIN_ID)
async def send_movie(message: Message, state: FSMContext):
    code = message.text.strip()
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await message.answer(
            "❌ <b>Bunday kodli kino topilmadi.</b>\nKodni tekshirib, qaytadan urinib ko'ring.",
            reply_markup=user_cancel_search_kb(),
            parse_mode="HTML"
        )
        return

    # Kino muvaffaqiyatli topilsa, holatni tozalaymiz va bosh menyu tugmasini ochamiz
    await state.clear()
    await message.answer_video(
        video=movie["file_id"],
        caption=f"🎬 <b>{movie['title']}</b>\n🔑 Kod: {movie['code']}\n📦 Turi: {movie['movie_type'].upper()}",
        parse_mode="HTML",
        reply_markup=yana_kino_kb()
    )
    # Bosh menyu tugmalarini pastda ko'rsatish
    await message.answer("Bosh menyu 👇", reply_markup=user_main_kb())
# ═══════════════════════════════════════════════
#         FOYDALANUVCHI — /about va /xatolik
# ═══════════════════════════════════════════════

@dp.message(Command("about"))
async def about_cmd(message: Message):
    await message.answer(
        f"ℹ️ <b>Bot haqida</b>\n\n"
        f"🎬 Bu bot orqali istalgan kinongizni kodini kiritib topishingiz mumkin.\n"
        f"Savollar yoki takliflar bo'lsa adminga murojaat qiling.\n\n"
        f"👨‍💻 Admin: {ADMIN_USERNAME}",
        parse_mode="HTML"
    )

@dp.message(Command("xatolik"), F.from_user.id != ADMIN_ID)
async def report_error_start(message: Message, state: FSMContext):
    await state.set_state(UserState.waiting_error)
    await message.answer("✍️ <b>Xatolik haqida xabaringizni yozing:</b>", parse_mode="HTML")

@dp.message(UserState.waiting_error, F.from_user.id != ADMIN_ID)
async def report_error_finish(message: Message, state: FSMContext):
    await state.clear()
    if not message.text:
        await message.answer("⚠️ Iltimos, faqat matn ko'rinishida yozing.")
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else "yo'q"
    try:
        await bot.send_message(
            ADMIN_ID,
            f"⚠️ <b>Yangi xatolik xabari</b>\n\n👤 Ism: {user.full_name}\n🔗 Username: {username}\n🆔 ID: <code>{user.id}</code>\n\n📝 <b>Xabar:</b>\n{message.text}",
            parse_mode="HTML"
        )
        await message.answer("✅ Xabaringiz adminga yuborildi!", reply_markup=user_main_kb())
    except Exception:
        await message.answer("❌ Xabar yuborishda xatolik bo'ldi.", reply_markup=user_main_kb())

@dp.callback_query(F.data.startswith("rate_"))
async def rating_callback(call: CallbackQuery):
    rating = int(call.data.split("_")[1])
    db.add_rating(call.from_user.id, rating)
    await call.message.edit_text(f"🙏 Rahmat! Botni {rating}⭐ baholadingiz.")

# ═══════════════════════════════════════════════
#                  ADMIN PANEL
# ═══════════════════════════════════════════════

@dp.message(CommandStart(), F.from_user.id == ADMIN_ID)
async def admin_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 Xush kelibsiz, Admin!", reply_markup=admin_main_kb())

@dp.message(F.text == "🎬 Kino bo'limi", F.from_user.id == ADMIN_ID)
async def admin_movie_section(message: Message):
    await message.answer("🎬 <b>Kino bo'limi</b>\nKerakli amalni tanlang 👇", reply_markup=admin_movie_kb(), parse_mode="HTML")

@dp.message(F.text == "📢 Kanal bo'limi", F.from_user.id == ADMIN_ID)
async def admin_channel_section(message: Message):
    await message.answer("📢 <b>Kanal bo'limi</b>\nKerakli amalni tanlang 👇", reply_markup=admin_channel_kb(), parse_mode="HTML")

@dp.message(F.text == "⬅️ Orqaga", F.from_user.id == ADMIN_ID)
async def admin_back_to_main(message: Message):
    await message.answer("🏠 <b>Asosiy menyu</b>", reply_markup=admin_main_kb(), parse_mode="HTML")

# ── KINO QO'SHISH (INLINE BILAN TURI SO'RALADI) ──────────

@dp.message(F.text == "➕ Kino qo'shish", F.from_user.id == ADMIN_ID)
async def admin_movie_add_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.movie_type)
    await message.answer("Kino turini tanlang:", reply_markup=admin_movie_type_kb())

@dp.callback_query(AdminState.movie_type, F.data.startswith("type_"))
async def admin_movie_type_selected(call: CallbackQuery, state: FSMContext):
    m_type = call.data.split("_")[1]
    await state.update_data(movie_type=m_type)
    await state.set_state(AdminState.movie_video)
    await call.message.delete()
    await call.message.answer("🎬 <b>Kino faylini (video yoki hujjat) yuboring:</b>", reply_markup=admin_cancel_kb(), parse_mode="HTML")

@dp.message(AdminState.movie_video, F.from_user.id == ADMIN_ID)
async def admin_movie_add_video(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_movie_kb())
        return

    file_id = message.video.file_id if message.video else (message.document.file_id if message.document else None)
    if not file_id:
        await message.answer("⚠️ Iltimos, faqat video yoki hujjat faylini yuboring!")
        return

    await state.update_data(file_id=file_id)
    await state.set_state(AdminState.movie_code)
    await message.answer("🔢 <b>Kino kodini kiriting:</b>", parse_mode="HTML")

@dp.message(AdminState.movie_code, F.from_user.id == ADMIN_ID)
async def admin_movie_add_code(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_movie_kb())
        return

    code = message.text.strip().upper()
    if db.get_movie_by_code(code):
        await message.answer(f"❌ <b>{code}</b> kodi band! Boshqa kod kiriting:")
        return

    await state.update_data(code=code)
    await state.set_state(AdminState.movie_title)
    await message.answer("✏️ <b>Kino sarlavhasini kiriting:</b>", parse_mode="HTML")

@dp.message(AdminState.movie_title, F.from_user.id == ADMIN_ID)
async def admin_movie_add_finish(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_movie_kb())
        return

    title = message.text.strip()
    data = await state.get_data()
    await state.clear()

    if db.add_movie(data["code"], title, data["file_id"], data["movie_type"]):
        await message.answer(f"✅ <b>Kino qo'shildi!</b>\n\n📌 Nomi: {title}\n🔢 Kodi: {data['code']}\n📦 Turi: {data['movie_type'].upper()}", reply_markup=admin_movie_kb(), parse_mode="HTML")
    else:
        await message.answer("❌ Xatolik yuz berdi.", reply_markup=admin_movie_kb())

# ── BOR KINOLAR RO'YXATI ─────────────────────────────────

@dp.message(F.text == "📋 Bor kinolar ro'yxati", F.from_user.id == ADMIN_ID)
async def admin_list_movies(message: Message):
    movies = db.get_all_movies()
    if not movies:
        await message.answer("📭 Bazada kinolar yo'q.")
        return
    
    text = "🎞 <b>Bazada bor kinolar ro'yxati (Tekin + Pullik):</b>\n\n"
    for m in movies:
        text += f"• <code>{m['code']}</code> — {m['title']} | <b>{m['movie_type'].upper()}</b>\n"
    
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "🗑 Kino o'chirish", F.from_user.id == ADMIN_ID)
async def admin_movie_delete_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.delete_code)
    await message.answer("🗑 O'chirmoqchi bo'lgan kino kodini yuboring:", reply_markup=admin_cancel_kb())

@dp.message(AdminState.delete_code, F.from_user.id == ADMIN_ID)
async def admin_movie_delete_finish(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_movie_kb())
        return
    await state.clear()
    if db.delete_movie(message.text.strip()):
        await message.answer("✅ Kino o'chirildi!", reply_markup=admin_movie_kb())
    else:
        await message.answer("❌ Kod topilmadi!", reply_markup=admin_movie_kb())

# ── KANAL QO'SHISH (INLINE BILAN PLATFORMA SO'RALADI) ─────

@dp.message(F.text == "➕ Kanal qo'shish", F.from_user.id == ADMIN_ID)
async def admin_channel_add_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.ch_platform)
    await message.answer("Kanal qaysi platformaga tegishli?", reply_markup=admin_platform_kb())

@dp.callback_query(AdminState.ch_platform, F.data.startswith("plat_"))
async def admin_channel_plat_selected(call: CallbackQuery, state: FSMContext):
    platform = call.data.split("_")[1]
    await state.update_data(platform=platform)
    await state.set_state(AdminState.ch_id)
    await call.message.delete()
    await call.message.answer(f"➕ <b>[{platform.upper()}] Kanal ID yoki Username kiriting:</b>\n<i>Telegram uchun ID, qolganlar uchun ixtiyoriy belgi</i>", reply_markup=admin_cancel_kb(), parse_mode="HTML")

@dp.message(AdminState.ch_id, F.from_user.id == ADMIN_ID)
async def admin_channel_add_id(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_channel_kb())
        return
    await state.update_data(ch_id=message.text.strip())
    await state.set_state(AdminState.ch_title)
    await message.answer("✏️ <b>Kanal nomini kiriting:</b>", parse_mode="HTML")

@dp.message(AdminState.ch_title, F.from_user.id == ADMIN_ID)
async def admin_channel_add_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_channel_kb())
        return
    await state.update_data(ch_title=message.text.strip())
    await state.set_state(AdminState.ch_link)
    await message.answer("🔗 <b>Kanal linkini kiriting:</b>", parse_mode="HTML")

@dp.message(AdminState.ch_link, F.from_user.id == ADMIN_ID)
async def admin_channel_add_link(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_channel_kb())
        return
    await state.update_data(ch_link=message.text.strip())
    await state.set_state(AdminState.ch_subs)
    await message.answer("👥 <b>Kanalda qancha obunachi bor? (Raqamda):</b>", parse_mode="HTML")

@dp.message(AdminState.ch_subs, F.from_user.id == ADMIN_ID)
async def admin_channel_add_finish(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_channel_kb())
        return
    
    try:
        subs = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Iltimos, obunachilar sonini faqat raqamda kiriting:")
        return

    data = await state.get_data()
    await state.clear()

    if db.add_channel(data["ch_id"], data["ch_title"], data["ch_link"], data["platform"], subs):
        await message.answer(f"✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\nPlatforma: {data['platform'].upper()}\nNomi: {data['ch_title']}\nObunachilar: {subs} ta", reply_markup=admin_channel_kb(), parse_mode="HTML")
    else:
        await message.answer("❌ Bu kanal oldin qo'shilgan yoki xatolik bo'ldi.", reply_markup=admin_channel_kb())

# ── BOR KANALLAR RO'YXATI HANDLERLARI (main.py ICHIDA) ──

@dp.message(F.text == "📋 Bor kanallar ro'yxati", F.from_user.id == ADMIN_ID)
async def admin_list_channels(message: Message):
    platforms = ['telegram', 'instagram', 'youtube']
    text = "📋 <b>Mavjud kanallar ro'yxati:</b>\n\n"
    
    for plat in platforms:
        text += f"🔹 <b>{plat.upper()} kanallari:</b>\n"
        channels = db.get_channels_by_platform(plat)
        if not channels:
            text += "<i>Ushbu platformada kanallar yo'q</i>\n"
        else:
            for ch in channels:
                # Agar havola to'liq (http) bo'lsa o'zi olinadi, aks holda t.me/ qo'shiladi
                link = ch['link']
                if not link.startswith(('http://', 'https://')):
                    link = f"https://{link}"
                
                # Kanal nomi ustiga bosganda kiradigan havola qilindi
                text += f" • <a href='{link}'>{ch['title']}</a> | 👤 {ch['sub_count']} obunachi | ID: <code>{ch['channel_id']}</code>\n"
        text += "\n"
        
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(F.text == "🗑 Kanal o'chirish", F.from_user.id == ADMIN_ID)
async def admin_channel_remove_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.ch_remove)
    await message.answer("🗑 O'chirmoqchi bo'lgan kanal ID/Username'ini yuboring:", reply_markup=admin_cancel_kb())

@dp.message(AdminState.ch_remove, F.from_user.id == ADMIN_ID)
async def admin_channel_remove_finish(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_channel_kb())
        return
    await state.clear()
    if db.remove_channel(message.text.strip()):
        await message.answer("✅ Kanal olib tashlandi!", reply_markup=admin_channel_kb())
    else:
        await message.answer("❌ Bunday kanal topilmadi!", reply_markup=admin_channel_kb())

# ── STATISTIKA VA REKLAMA (ESKI FUNKSIYALARNING MOSLASHUVI) ──

@dp.message(F.text == "📊 Oylik statistika", F.from_user.id == ADMIN_ID)
async def admin_stats(message: Message):
    stats = db.get_monthly_stats()
    total = db.get_total_users()
    rating = db.get_monthly_rating()
    await message.answer(
        f"📊 <b>Oylik statistika ({stats['month']})</b>\n\n➕ Qo'shilganlar: <b>{stats['joined']}</b>\n➖ Chiqib ketganlar: <b>{stats['left']}</b>\n👥 Jami aktiv: <b>{total}</b>\n⭐ O'rtacha baho: <b>{rating['avg']}</b> ({rating['count']} ta baho)",
        parse_mode="HTML"
    )

@dp.message(F.text == "📣 Reklama", F.from_user.id == ADMIN_ID)
async def admin_advert_ask(message: Message, state: FSMContext):
    await state.set_state(AdminState.advert)
    await message.answer("📢 <b>Reklama xabarini yuboring:</b>", reply_markup=admin_cancel_kb(), parse_mode="HTML")

@dp.message(AdminState.advert, F.from_user.id == ADMIN_ID)
async def admin_advert_send(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
        return

    await state.clear()
    users = db.get_all_user_ids()
    ok, fail = 0, 0
    progress = await message.answer(f"⏳ Yuborilmoqda: 0/{len(users)}")

    for i, uid in enumerate(users, 1):
        try:
            await message.copy_to(uid)
            ok += 1
        except Exception:
            fail += 1
        if i % 30 == 0:
            try: await progress.edit_text(f"⏳ Yuborilmoqda: {i}/{len(users)}")
            except Exception: pass

    await progress.edit_text(f"✅ <b>Reklama yuborildi!</b>\n\n✅ Muvaffaqiyatli: {ok}\n❌ Yuborilmadi: {fail}", parse_mode="HTML")
    await message.answer("Bosh sahifa 👇", reply_markup=admin_main_kb())

@dp.message(F.text == "⭐ Reyting so'rash", F.from_user.id == ADMIN_ID)
async def admin_request_rating(message: Message):
    users = db.get_all_user_ids()
    ok, fail = 0, 0
    progress = await message.answer(f"⏳ Yuborilmoqda: 0/{len(users)}")

    for i, uid in enumerate(users, 1):
        try:
            await bot.send_message(uid, "🙏 <b>Botimizni baholab keting!</b>\n\nSizga bot qanchalik yoqdi?", reply_markup=rating_kb(), parse_mode="HTML")
            ok += 1
        except Exception:
            fail += 1
        if i % 30 == 0:
            try: await progress.edit_text(f"⏳ Yuborilmoqda: {i}/{len(users)}")
            except Exception: pass

    await progress.edit_text(f"✅ <b>Reyting so'rovi yuborildi!</b>\n\n✅ Muvaffaqiyatli: {ok}\n❌ Yuborilmadi: {fail}", parse_mode="HTML")
    await message.answer("Bosh sahifa 👇", reply_markup=admin_main_kb())

async def set_commands():
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni qayta ishga tushurish"),
        BotCommand(command="about", description="Bot haqida"),
        BotCommand(command="xatolik", description="Xatolik haqida adminga xabar berish"),
    ])

async def main():
    db.init_db()
    await set_commands()
    logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
