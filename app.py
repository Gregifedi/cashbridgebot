from flask import Flask, request
import requests

from core.rules import is_payment_message, extract_amount, extract_sender
from database.db import init_db, save_payment
from config import TELEGRAM_API  # ✅ now from env

app = Flask(__name__)

# Init DB once (safe wrap)
try:
    init_db()
    print("✅ DB initialized")
except Exception as e:
    print("❌ DB init failed:", e)


def send_message(chat_id, text):
    try:
        requests.post(TELEGRAM_API, json={
            "chat_id": chat_id,
            "text": text
        }, timeout=10)
    except Exception as e:
        print("Send error:", e)


@app.route("/", methods=["GET"])
def home():
    return "Bot is running"


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        if not data:
            return "no data", 400

        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if not chat_id:
            return "no chat_id", 400

        # Only process payment-like messages
        if is_payment_message(text):
            amount = extract_amount(text)
            sender = extract_sender(text)

            if amount > 0:
                save_payment(amount, sender, chat_id)

                send_message(chat_id,
                    f"✅ Payment saved\nAmount: {amount}\nSender: {sender}"
                )
            else:
                send_message(chat_id, "⚠️ Could not detect amount")

        return "ok", 200

    except Exception as e:
        print("🔥 WEBHOOK ERROR:", e)
        return "ok", 200


if __name__ == "__main__":
    app.run(port=5000)