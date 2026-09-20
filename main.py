import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InputMediaPhoto

# --- SOZLAMALAR ---
BOT_TOKEN = "8650992085:AAF4rp-9mJGibBJKNmZFLubf0kZJ63Cet4E"  # Bot tokeningiz
ADMIN_ID = 6735904763  # Admin ID (Siz kiritgan yangi ID)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# --- FSM (Holatlar zanjiri) ---
class ErtakBuyurtma(StatesGroup):
    user_name = State()       # 1. Foydalanuvchining ism-familiyasi
    bola_ismi = State()       # 2. Bolaning ismi va yoshi
    bola_rasmi = State()      # 📸 1 dan 30 tagacha rasm yig'ish joyi
    ertak_nomi = State()      # 3. Qaysi ertak ekanligi
    dostlari = State()        # 4. O'rtoqlarining ismi
    qiziqishlari = State()    # 5. Qiziqishlari
    ertak_goyasi = State()    # 6. Ertak haqida qisqacha fikri
    chek_kutish = State()     # 📥 Mijozdan to'lov chekini kutish holati

class AdminJavob(StatesGroup):
    target_client_id = State()
    narx_kutish = State()     # ✍️ Admin qo'lda narx va karta yozishi uchun holat
    pdf_kutish = State()

# --- KLAVIATURALAR ---
tugatdim_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📥 Rasm yuborishni tugatdim")]],
    resize_keyboard=True
)

# --- FOYDALANUVCHINI BOSHLANG'ICH NUQTAGA QAYTARISH FUNKSIYASI ---
async def start_order_process(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "✍️ **1. Ismingiz va familiyangizni kiriting:**",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ErtakBuyurtma.user_name)

# --- FOYDALANUVCHI QISMI ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await message.answer(
        "👋 Salom! Bolajonlar uchun sehrli va shaxsiylashtirilgan ertak buyurtma qilish botiga xush kelibsiz.\n\n"
        "Sizga va bolajoningizga mos ertak yaratishimiz uchun bir nechta savollarga javob bering."
    )
    await start_order_process(message, state)

@dp.callback_query(F.data == "reorder")
async def reorder_cmd(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("🎉 Yangi buyurtma berish jarayonini boshlaymiz!")
    await start_order_process(call.message, state)
    await call.answer()

@dp.message(ErtakBuyurtma.user_name)
async def get_user_name(message: types.Message, state: FSMContext):
    await state.update_data(user_name=message.text)
    await message.answer("👶 **2. Bolajonning ismi va yoshi nechada?**\n*(Masalan: Humoyun, 5 yosh)*")
    await state.set_state(ErtakBuyurtma.bola_ismi)

@dp.message(ErtakBuyurtma.bola_ismi)
async def get_child_info(message: types.Message, state: FSMContext):
    await state.update_data(bola_ismi=message.text)
    await state.update_data(bola_rasmi=[])
    await message.answer(
        "📸 **3. Bolajonning rasmini yuboring:**\n"
        "*(1 tadan 30 tagacha rasm yuborishingiz mumkin. Rasmlarni guruhlab-guruhlab jo'natishingiz mumkin. Tugatgach pastdagi tugmani bosing)*",
        reply_markup=tugatdim_kb
    )
    await state.set_state(ErtakBuyurtma.bola_rasmi)

@dp.message(ErtakBuyurtma.bola_rasmi, F.photo)
async def get_child_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rasmlar = data.get('bola_rasmi', [])
    
    if len(rasmlar) >= 30:
        await message.answer("❌ Maksimal 30 ta rasm yuborishingiz mumkin. Iltimos, keyingi bosqichga o'tish uchun pastdagi tugmani bosing.")
        return

    photo_id = message.photo[-1].file_id
    rasmlar.append(photo_id)
    await state.update_data(bola_rasmi=rasmlar)
    await message.answer(f"✅ Rasm qabul qilindi ({len(rasmlar)}/30).")

@dp.message(ErtakBuyurtma.bola_rasmi, F.text == "📥 Rasm yuborishni tugatdim")
async def finish_photo_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rasmlar = data.get('bola_rasmi', [])
    
    if not rasmlar:
        await message.answer("❌ Kamida 1 ta rasm yuborishingiz shart!")
        return

    await message.answer(
        "📖 **4. Qaysi ertak asosida bo'lishini xohlaysiz?**\n*(Masalan: Zumrad va Qimmat)*",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ErtakBuyurtma.ertak_nomi)

@dp.message(ErtakBuyurtma.bola_rasmi)
async def child_photo_invalid(message: types.Message):
    await message.answer("❌ Iltimos, rasm yuboring yoki **'📥 Rasm yuborishni tugatdim'** tugmasini bosing:")

@dp.message(ErtakBuyurtma.ertak_nomi)
async def get_story_theme(message: types.Message, state: FSMContext):
    await state.update_data(ertak_nomi=message.text)
    await message.answer("👬 **5. Ertakda ishtirok etadigan do'stlari yoki yaqinlarining ismlarini yozing:**")
    await state.set_state(ErtakBuyurtma.dostlari)

@dp.message(ErtakBuyurtma.dostlari)
async def get_friends(message: types.Message, state: FSMContext):
    await state.update_data(dostlari=message.text)
    await message.answer("🎨 **6. Bolaning asosiy qiziqishlari nimalar?**")
    await state.set_state(ErtakBuyurtma.qiziqishlari)

@dp.message(ErtakBuyurtma.qiziqishlari)
async def get_interests(message: types.Message, state: FSMContext):
    await state.update_data(qiziqishlari=message.text)
    await message.answer("✨ **7. Ertak qanday bo'lishi haqida qisqacha fikringiz (g'oyangiz):**")
    await state.set_state(ErtakBuyurtma.ertak_goyasi)

@dp.message(ErtakBuyurtma.ertak_goyasi)
async def get_story_idea(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    user_name = user_data['user_name']
    bola_ismi = user_data['bola_ismi']
    rasmlar = user_data['bola_rasmi']
    ertak_nomi = user_data['ertak_nomi']
    dostlari = user_data['dostlari']
    qiziqishlari = user_data['qiziqishlari']
    ertak_goyasi = message.text

    await state.set_state(None)
    await message.answer("🎉 Rahmat! Barcha ma'lumotlar va rasmlar muvaffaqiyatli qabul qilindi. Admin tez orada ertakni tayyorlab, sizga to'lov ma'lumotlarini yuboradi. Iltimos, kuting!")

    admin_text = (
        "🚨 **YANGI BUYURTMA KELDI!**\n\n"
        f"👤 **Mijoz ID:** `{message.from_user.id}`\n"
        f"✍️ **Foydalanuvchi:** {user_name}\n"
        f"👶 **Bola:** {bola_ismi}\n"
        f"📖 **Ertak nomi:** {ertak_nomi}\n"
        f"👬 **O'rtoqlari:** {dostlari}\n"
        f"🎨 **Qiziqishlari:** {qiziqishlari}\n"
        f"💡 **Fikri:** {ertak_goyasi}\n\n"
        f"📸 **Yuborilgan rasmlar soni:** {len(rasmlar)} ta\n\n"
        "Kerakli amalni tanlang:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 To'lov so'rash", callback_data=f"pay_{message.from_user.id}")],
        [InlineKeyboardButton(text="📂 PDF Ertakni Yuklash", callback_data=f"sendpdf_{message.from_user.id}")]
    ])
    
    try:
        chunks = [rasmlar[i:i + 10] for i in range(0, len(rasmlar), 10)]
        for index, chunk in enumerate(chunks):
            media_group = []
            for j, photo_id in enumerate(chunk):
                if index == 0 and j == 0:
                    media_group.append(InputMediaPhoto(media=photo_id, caption=admin_text))
                else:
                    media_group.append(InputMediaPhoto(media=photo_id))
            await bot.send_media_group(chat_id=ADMIN_ID, media=media_group)
            await asyncio.sleep(0.5)
        await bot.send_message(chat_id=ADMIN_ID, text="⚙️ **Boshqaruv paneli:**", reply_markup=keyboard)
    except Exception:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=keyboard)

# --- MIJOZDAN TO'LOV CHEKINI QABUL QILISH JRAYONI ---
@dp.message(ErtakBuyurtma.chek_kutish, F.photo | F.document)
async def user_send_receipt(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    client_name = user_data.get('user_name', message.from_user.full_name)
    
    await state.clear()
    await message.answer("✅ Chek qabul qilindi va adminga yuborildi! To'lov tasdiqlangach, ertak kitobingiz yuboriladi. ✨")
    
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 PDF Ertakni Yuklash", callback_data=f"sendpdf_{message.from_user.id}")]
    ])
    
    caption_text = (
        "🧾 **MIJOZDAN TO'LOV CHEKI KELDI!**\n\n"
        f"👤 **Mijoz:** {client_name}\n"
        f"🆔 **ID raqami:** `{message.from_user.id}`"
    )
    
    if message.photo:
        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption_text, reply_markup=admin_keyboard)
    elif message.document:
        await bot.send_document(chat_id=ADMIN_ID, document=message.document.file_id, caption=caption_text, reply_markup=admin_keyboard)

# --- ADMIN PROCESSORS ---
@dp.callback_query(F.data.startswith("pay_"))
async def admin_ask_payment(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split("_")[1])
    await state.update_data(target_client_id=client_id)
    await state.set_state(AdminJavob.narx_kutish)
    await call.message.answer(f"✍️ ` [{client_id}] ` ID li mijoz uchun **ertak narxi va karta raqamini** qo'lda yozib yuboring:")
    await call.answer()

@dp.message(AdminJavob.narx_kutish, F.text)
async def admin_send_custom_payment(message: types.Message, state: FSMContext):
    admin_data = await state.get_data()
    client_id = admin_data['target_client_id']
    custom_text = message.text
    
    try:
        await dp.fsm.get_context(bot=bot, chat_id=client_id, user_id=client_id).set_state(ErtakBuyurtma.chek_kutish)
        await bot.send_message(chat_id=client_id, text=custom_text)
        await message.answer(f"✅ Mijozga to'lov ma'lumotlari yuborildi va bot undan chek kutmoqda.")
    except Exception as e:
        await message.answer(f"Mijozga yuborishda xatolik yuz berdi: {e}")
    await state.clear()

@dp.callback_query(F.data.startswith("sendpdf_"))
async def admin_prepare_pdf(call: types.CallbackQuery, state: FSMContext):
    client_id = int(call.data.split("_")[1])
    
    client_state = dp.fsm.get_context(bot=bot, chat_id=client_id, user_id=client_id)
    client_data = await client_state.get_data()
    client_name = client_data.get('user_name', f"ID: {client_id}")

    await state.update_data(target_client_id=client_id)
    await state.set_state(AdminJavob.pdf_kutish)
    await call.message.answer(f"📁 Iltimos, **{client_name}** uchun tayyorlangan ertak kitobining **PDF faylini** botga yuklang:")
    await call.answer()

    await state.clear()

# --- RENDER PORT BINDING VA BOTNI ISHGA TUSHIRISH (FAQAT SHU BLOK QOLADI) ---
import os
from aiohttp import web

# Render portni topishi va xato bermasligi uchun soxta sahifa
async def handle(request):
    return web.Response(text="Ertak Bot muvaffaqiyatli ishlamoqda!")

async def on_startup_tasks(app):
    # 1. Eski webhooklarni (kesh xabarlarni) tozalaymiz
    await bot.delete_webhook(drop_pending_updates=True)
    # 2. Botingizni orqa fonda (polling rejimida) ishga tushiramiz
    asyncio.create_task(dp.start_polling(bot))

async def init_app():
    app = web.Application()
    app.router.add_get('/', handle)
    app.on_startup.append(on_startup_tasks)
    return app

if __name__ == '__main__':
    try:
        # Render taqdim etadigan portni o'qib olamiz, bo'lmasa 8080 ni oladi
        port = int(os.environ.get("PORT", 8080))
        app = asyncio.run(init_app())
        web.run_app(app, host='0.0.0.0', port=port)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
