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

# Handlerlarni import qilish
try:
    from app.bot.handlers import router as registration_router
except ImportError:
    registration_router = None

API_BASE_URL = "http://127.0.0.1:8000"
BOT_TOKEN = "8542032478:AAHD-gX0AVdt2NPcd8NtfoBaw3hD9_J6HMY"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, state: FSMContext):
    args = command.args
    if not args:
        await message.answer("❌ Iltimos, botga sayt orqali kiring (Raqamingiz tasdiqlanmagan).")
        return

    # 1. Saytdan kelgan raqamni tozalash
    # %20, bo'shliq va + belgilarini olib tashlaymiz
    raw_phone = args.replace("%20", "").replace(" ", "").replace("+", "").strip()
    clean_phone = re.sub(r'\D', '', raw_phone)
    
    url = f"{API_BASE_URL}/v1/api/auth/bot/start"
    payload = {
        "phone": clean_phone,
        "telegram_id": str(message.from_user.id),
        "full_name": message.from_user.full_name or "Unknown"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    is_new_user = data.get("is_new_user")
                    code = data.get("code")

                    # --- SENARIY 1: YANGI USER (Registratsiya kerak) ---
                    if is_new_user:
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="start_register_flow")]
                        ])
                        
                        # FSM ga telefonni saqlaymiz, registratsiya handlerlari foydalanishi uchun
                        await state.update_data(phone=clean_phone)
                        
                        await message.answer(
                            f"👋 <b>Salom!</b>\n\n"
                            f"Sizning raqamingiz (<code>{clean_phone}</code>) bazada topilmadi.\n"
                            "Xizmatlardan foydalanish uchun ro'yxatdan o'ting:",
                            reply_markup=kb
                        )

                    # --- SENARIY 2: MAVJUD USER (Login uchun kod) ---
                    else:
                        await message.answer(
                            "🔐 <b>Tasdiqlash kodi</b>\n\n"
                            f"<pre>{code}</pre>\n\n"
                            "⏳ Kod 5 daqiqa amal qiladi.\n"
                            "🌐 Uni saytga qaytib kiriting."
                        )
                else:
                    error_data = await response.json()
                    detail = error_data.get('detail', 'Noma\'lum xatolik')
                    await message.answer(f"❌ Xatolik: {detail}")

    except aiohttp.ClientConnectorError:
        await message.answer("❌ Backend serverga ulanib bo'lmadi. Server yoniqligini tekshiring.")
    except Exception as e:
        logging.exception("Kutilmagan xatolik:")
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Routerlarni qo'shish (Tartib muhim: avval registratsiya, keyin start)
    if registration_router:
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