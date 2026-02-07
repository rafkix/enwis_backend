import os
from dotenv import load_dotenv

load_dotenv()

# =====================
# SECURITY
# =====================
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
AUDIENCE = os.getenv("AUDIENCE", "enwis")

ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", 1440))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", 30))
INTERNAL_API_TOKEN = "rafkix1234"


# =====================
# COOKIE
# =====================
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".enwis.uz")

# =====================
# CORS
# =====================
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://app.enwis.uz,https://cefr.enwis.uz,https://ielts.enwis.uz"
).split(",")

# =====================
# TELEGRAM
# =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
