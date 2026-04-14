from flask import Flask, request
import requests
import os

from core.rules import is_payment_message, extract_amount
from config import BOT_TOKEN, OWNER_CHAT_ID, TELEGRAM_API
from database.db import init_db, save_payment

app = Flask(__name__)

# Initialize database
init_db()


def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code != 200:
            print(f"Telegram API error: {response.text}")

    except Exception as e:
        print(f"Send message error: {e}")


@app.route("/", methods=["GET"])
def home():
    return "CashBridgeBot is running"


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        if not data:
            return "no data", 200

        print("Incoming update:", data)

        if "message" in data:
            msg = data["message"]

            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")

            # START COMMAND
            if text == "/start":
                send_message(chat_id, "CashBridgeBot online. Ready.")

            # PAYMENT DETECTION
            elif is_payment_message(text):

                amount = extract_amount(text)

                # SAVE TO DATABASE
                save_payment(amount if amount else "unknown", text)

                if amount:
                    send_message(chat_id, f"💰 Payment detected: ₦{amount}")

                    if OWNER_CHAT_ID:
                        send_message(
                            OWNER_CHAT_ID,
                            f"💰 PAYMENT ALERT\nAmount: ₦{amount}\n\n{text}"
                        )
                else:
                    send_message(chat_id, "💰 Payment detected")

                    if OWNER_CHAT_ID:
                        send_message(
                            OWNER_CHAT_ID,
                            f"💰 PAYMENT ALERT (NO AMOUNT)\n\n{text}"
                        )

            # NORMAL MESSAGE
            else:
                send_message(chat_id, f"You said: {text}")

                if OWNER_CHAT_ID:
                    send_message(
                        OWNER_CHAT_ID,
                        f"📩 New message:\n{text}"
                    )

        return "ok", 200

    except Exception as e:
        print(f"Webhook error: {e}")
        return "error", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)















