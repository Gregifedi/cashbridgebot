from flask import Flask, request
import requests

from core.rules import is_payment_message, extract_amount, extract_sender
from database.db import init_db, save_payment

# CONFIG
TELEGRAM_TOKEN = "bot8770663127:AAHZHL4fPgff6sRvgRHYd_fRL4TzezkyXJ8"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

app = Flask(__name__)

# Init DB once
init_db()


def send_message(chat_id, text):
    requests.post(TELEGRAM_API, json={
        "chat_id": chat_id,
        "text": text
    })


@app.route("/", methods=["GET"])
def home():
    return "Bot is running"


@app.route("/webhook", methods=["POST"])
def webhook():
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

            send_message(chat_id, f"✅ Payment saved\nAmount: {amount}\nSender: {sender}")
        else:
            send_message(chat_id, "⚠️ Could not detect amount")

    return "ok", 200


if __name__ == "__main__":
    app.run(port=5000)










