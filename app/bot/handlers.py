import re
import aiohttp
import logging
from aiogram import Router, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, 
    ReplyKeyboardRemove, CallbackQuery
)
from aiogram.fsm.context import FSMContext
from app.bot.states import UserRegisterState

router = Router()
API_BASE_URL = "http://127.0.0.1:8000"

# --- 1. RO'YXATDAN O'TISHNI BOSHLASH ---
@router.callback_query(F.data == "start_register_flow")
async def callback_register(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("📝 <b>Ro'yxatdan o'tish boshlandi.</b>\n\nIltimos, <b>To'liq ismingizni</b> kiriting:",parse_mode="HTML")
    await state.set_state(UserRegisterState.waiting_for_full_name)

# --- 2. ISM -> USERNAME ---
@router.message(UserRegisterState.waiting_for_full_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("✅ Qabul qilindi. Endi <b>Username</b> tanlang (faqat lotin harflari va sonlar):", parse_mode="HTML")
    await state.set_state(UserRegisterState.waiting_for_username)

# --- 3. USERNAME -> EMAIL ---
@router.message(UserRegisterState.waiting_for_username)
async def get_username(message: Message, state: FSMContext):
    if not re.match(r'^[a-zA-Z0-9_]+$', message.text):
        return await message.answer("❌ Username noto'g'ri. Qayta urinib ko'ring:")
    await state.update_data(username=message.text)
    await message.answer("📧 <b>Email</b> manzilingizni kiriting:", parse_mode="HTML")
    await state.set_state(UserRegisterState.waiting_for_email)

# --- 4. EMAIL -> PAROL ---
@router.message(UserRegisterState.waiting_for_email)
async def get_email(message: Message, state: FSMContext):
    if "@" not in message.text:
        return await message.answer("❌ Noto'g'ri email. Qayta kiriting:")
    await state.update_data(email=message.text)
    await message.answer("🔒 Tizim uchun <b>Parol</b> yarating (kamida 6 ta belgi):", parse_mode="HTML")
    await state.set_state(UserRegisterState.waiting_for_password)

# --- 5. PAROL -> YOSH ---
@router.message(UserRegisterState.waiting_for_password)
async def get_password(message: Message, state: FSMContext):
    if len(message.text) < 6:
        return await message.answer("❌ Parol juda qisqa. Qayta kiriting:")
    await state.update_data(password=message.text)
    await message.answer("🔢 <b>Yoshingizni</b> kiriting (faqat raqamda):", parse_mode="HTML")
    await state.set_state(UserRegisterState.waiting_for_age)

# --- 6. YOSH -> LEVEL ---
@router.message(UserRegisterState.waiting_for_age)
async def get_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Faqat raqam kiriting:")
    await state.update_data(age=int(message.text))
    
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="beginner"), KeyboardButton(text="elementary")],
            [KeyboardButton(text="intermediate"), KeyboardButton(text="advanced")]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("📊 <b>Ingliz tili darajangizni</b> tanlang:", reply_markup=kb, parse_mode="HTML")
    await state.set_state(UserRegisterState.waiting_for_level)

# --- 7. LEVEL -> TELEFON (OXIRGI BOSQICH) ---
@router.message(UserRegisterState.waiting_for_level)
async def get_level(message: Message, state: FSMContext):
    await state.update_data(level=message.text)
    
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("📱 Ro'yxatdan o'tishni yakunlash uchun <b>Telefon raqamingizni</b> yuboring:", reply_markup=kb, parse_mode="HTML")
    await state.set_state(UserRegisterState.waiting_for_phone)

@router.message(UserRegisterState.waiting_for_phone)
async def finish_registration(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    clean_phone = re.sub(r'\D', '', str(phone))
    
    if len(clean_phone) < 9:
        await message.answer("❌ Noto'g'ri telefon raqami. Iltimos, qaytadan yuboring:")
        return

    user_data = await state.get_data()
    
    register_payload = {
        "full_name": user_data.get('full_name'),
        "username": user_data.get('username'),
        "email": user_data.get('email'),
        "password": user_data.get('password'),
        "phone": clean_phone,
        "age": int(user_data.get('age', 0)),
        "level": user_data.get('level', 'beginner'),
        "telegram_id": str(message.from_user.id),
        "role": "student",
    }
    
    status_msg = await message.answer("⏳ Hisob yaratilmoqda...", reply_markup=ReplyKeyboardRemove())

    async with aiohttp.ClientSession() as session:
        try:
            reg_url = f"{API_BASE_URL}/v1/api/auth/register/telegram"
            async with session.post(reg_url, json=register_payload, timeout=20) as reg_resp:
                if reg_resp.status in [200, 201]:
                    start_url = f"{API_BASE_URL}/v1/api/auth/bot/start"
                    start_payload = {
                        "phone": clean_phone,
                        "telegram_id": str(message.from_user.id),
                        "full_name": user_data.get('full_name')
                    }
                    
                    async with session.post(start_url, json=start_payload) as start_resp:
                        if start_resp.status == 200:
                            data = await start_resp.json()
                            login_code = data.get("code")
                            
                            # Xabarni o'chirishda xatolik bo'lsa ham davom etish
                            try:
                                await status_msg.delete()
                            except:
                                pass

                            await message.answer(
                                f"✅ <b>Tabriklaymiz! Ro'yxatdan o'tdingiz.</b>\n\n"
                                f"👤 F.I.SH: <code>{user_data.get('full_name')}</code>\n"
                                f"📞 Tel: <code>{clean_phone}</code>\n\n"
                                f"🔐 Saytga kirish uchun kodingiz:\n"
                                f"<b><pre>{login_code}</pre></b>\n\n"
                                f"🌐 Saytga qaytib ushbu kodni kiriting.",
                                parse_mode="HTML"
                            )
                            await state.clear()
                        else:
                            await message.answer("✅ Ro'yxatdan o'tdingiz, lekin kod olishda xatolik bo'ldi.")
                            await state.clear()
                
                else:
                    err_data = await reg_resp.json()
                    detail = err_data.get('detail', 'Xato yuz berdi')
                    if isinstance(detail, list):
                        detail = detail[0].get('msg', 'Ma\'lumotlar xato')
                    
                    # Edit text o'rniga yangi xabar yuborish xavfsizroq
                    await message.answer(f"❌ Xatolik: {detail}")

        except Exception as e:
            logging.error(f"Bot Registration Error: {e}")
            await message.answer(f"❌ Tizimda xatolik yuz berdi. Iltimos keyinroq urinib ko'ring.")