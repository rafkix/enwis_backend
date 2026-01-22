import asyncio
import logging
import aiohttp
import re

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, CommandObject
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from app.bot.handlers import router as registration_router

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


API_BASE_URL = "https://api.enwis.uz"
BOT_TOKEN = "8542032478:AAHD-gX0AVdt2NPcd8NtfoBaw3hD9_J6HMY"


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, state: FSMContext):
    args = command.args
    
    # --- ASOSIY MENYU (Tugmalar) ---
    # Saytga o'tish va Web App tugmalari
    main_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Web App-ni ochish", web_app={"url": "https://cefr.enwis.uz"})]
    ])

    if not args:
        await message.answer(
            "👋 <b>Enwis botiga xush kelibsiz!</b>\n\n"
            "Platformadan foydalanish uchun saytimizga tashrif buyuring:",
            reply_markup=main_kb
        )
        return

    # 1. Saytdan kelgan raqamni tozalash
    raw_phone = args.replace("%20", "").replace(" ", "").replace("+", "").strip()
    clean_phone = re.sub(r'\D', '', raw_phone)
    
    # 2. Payloadni Backend Schemasiga (BotStartRequest) moslash
    url = f"{API_BASE_URL}/v1/api/auth/bot/start"
    payload = {
        "phone": clean_phone,
        "telegram_id": int(message.from_user.id),
        "full_name": message.from_user.full_name or "Unknown User"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    is_new_user = data.get("is_new_user")
                    code = data.get("code")

                    if is_new_user:
                        # Registratsiya uchun inline tugma
                        reg_kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="start_register_flow")],
                            [InlineKeyboardButton(text="🌐 Saytga qaytish", url="https://enwis.uz")]
                        ])
                        
                        await state.update_data(phone=clean_phone, telegram_id=int(message.from_user.id))
                        
                        await message.answer(
                            f"👋 <b>Salom!</b>\n\n"
                            f"Sizning raqamingiz (<code>{clean_phone}</code>) bazada topilmadi.\n"
                            "Xizmatlardan foydalanish uchun ro'yxatdan o'ting:",
                            reply_markup=reg_kb
                        )
                    else:
                        # Login kodi bilan birga saytga qaytish tugmasi
                        login_kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🌐 Saytga o'tish", url="https://enwis.uz")]
                        ])
                        
                        await message.answer(
                            "🔐 <b>Tasdiqlash kodi</b>\n\n"
                            f"<code>{code}</code>\n\n"
                            "⏳ Kod 10 daqiqa amal qiladi.\n"
                            "🌐 Uni saytga qaytib kiriting.",
                            reply_markup=login_kb
                        )
                else:
                    await message.answer("❌ Backend xatoligi yoki noto'g'ri so'rov.", reply_markup=main_kb)

    except Exception as e:
        logging.exception("Start Handler Error:")
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}", reply_markup=main_kb)
        
        
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Routerlarni qo'shish (Tartib muhim: avval registratsiya, keyin start)
    dp.include_router(registration_router)
    dp.include_router(router)
    
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    async def run():
        try:
            await main()
        except KeyboardInterrupt:
            print("Bot to'xtatildi")

    asyncio.run(run())
