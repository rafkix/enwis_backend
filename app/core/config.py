import os
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

# 🗃 Database
DB_PATH = os.getenv("DB_PATH", "enwis.db")

# 🔐 JWT
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", 60))
OPENAI_API_KEY = str(os.getenv("OPENAI_API_KEY", ""))

# 🌐 OAuth (external logins)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "9324f246c7ef4e887bff6bcdfd4815f91969fed11e4742b2b47bf0d0b1eb6a02")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "TxGEqnHWrfWFTfGW9XjX")


# (Optional) debug uchun
if not GOOGLE_CLIENT_ID:
    print("⚠️ GOOGLE_CLIENT_ID not set")
if not TELEGRAM_BOT_TOKEN:
    print("⚠️ TELEGRAM_BOT_TOKEN not set")
