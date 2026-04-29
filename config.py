import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set in environment variables")

# Build Telegram API endpoint
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"