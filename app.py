from flask import Flask, request
import requests
import os

from core.rules import is_payment_message, extract_amount
from config import OWNER_CHAT_ID, TELEGRAM_API

from database.db import (
    init_db,
    save_payment,
    get_total,
    get_today_total,
    get_count,
    get_top_sender,
    save_user,
    update_user_email,
    get_email_by_chat,
    get_user_history
)

app = Flask(__name__)
init_db()


def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
    except Exception as e:
        print("Send error:", e)


@app.route("/")
def home():
    return "CashBridgeBot is running"


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        msg = data.get("message") or data.get("edited_message") or data.get("channel_post")
        if not msg:
            return "ok", 200

        chat_id = msg["chat"]["id"]
        text = msg.get("text") or msg.get("caption") or ""
        text = text.strip()

        user = msg.get("from", {})
        username = user.get("username") or str(chat_id)

        # ---------------- COMMANDS ----------------

        if text == "/start":
            send_message(chat_id, "Bot is alive")

        elif text == "/pay":
            send_message(chat_id, "💳 Payment system active")

        elif text.startswith("/link"):
            parts = text.split(" ", 1)
            if len(parts) > 1:
                email = parts[1].strip().lower()
                save_user(chat_id, username)
                update_user_email(chat_id, email)
                send_message(chat_id, f"✅ Linked to {email}")
            else:
                send_message(chat_id, "Usage: /link email")

        elif text == "/stats":
            send_message(chat_id,
                f"Total: ₦{get_total()}\n"
                f"Today: ₦{get_today_total()}\n"
                f"Count: {get_count()}\n"
                f"Top: {get_top_sender()}"
            )

        elif text == "/history":
            history = get_user_history()

            if not history:
                send_message(chat_id, "No payment history found.")
            else:
                msg_out = "🧾 Last Payments:\n\n"
                for i, (amount, created_at) in enumerate(history, 1):
                    msg_out += f"{i}. ₦{amount} — {created_at[:10]}\n"

                send_message(chat_id, msg_out)

        # ---------------- PAYMENT ----------------

        elif is_payment_message(text):
            amount = extract_amount(text)

            save_payment(amount, text, sender=username)

            send_message(chat_id, f"✅ Payment received: ₦{amount}")

            if OWNER_CHAT_ID:
                send_message(OWNER_CHAT_ID, f"PAYMENT: ₦{amount}\n{text}")

        return "ok", 200

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "error", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)












