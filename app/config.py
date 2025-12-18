# import os
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

# 🗃 Database
DB_PATH = "walle.db"

# 🔐 JWT
SECRET_KEY = "rafkix"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 120

# 🌐 OAuth (external logins)
GOOGLE_CLIENT_ID="260764636744-0iukf6ukmljlatu0ulfrcl96s87e13l5.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="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"
TELEGRAM_BOT_TOKEN="8542032478:AAFzdZ8JnvL4gGYugIEPs1GMEA0gdQU7reo"

ALLOWED_ORIGINS = ["*", "enwis.uz", "www.enwis.uz", "api.enwis.uz", "app.enwis.uz"]

ELEVENLABS_API_KEY = "9324f246c7ef4e887bff6bcdfd4815f91969fed11e4742b2b47bf0d0b1eb6a02"
ELEVENLABS_VOICE_ID = "TxGEqnHWrfWFTfGW9XjX"
