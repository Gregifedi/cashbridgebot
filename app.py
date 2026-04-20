from flask import Flask, request
import requests
import os
import hashlib
import hmac

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
    get_user_by_email,
    get_user_total,
    get_user_today,
    get_user_last,
    get_user_history
)

app = Flask(__name__)

init_db()


def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print("Send error:", e)


@app.route("/")
def home():
    return "CashBridgeBot is running"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if not data or "message" not in data:
        return "ok", 200

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    username = msg.get("chat", {}).get("username", "unknown")

    if text == "/start":
        send_message(chat_id, "Bot is alive")

    elif text == "/link":
        send_message(chat_id, "Usage: /link email@example.com")

    elif text.startswith("/link"):
        email = text.split(" ", 1)[1].strip().lower()
        save_user(chat_id, username)
        update_user_email(chat_id, email)
        send_message(chat_id, f"✅ Linked to {email}")

    elif text == "/total":
        send_message(chat_id, f"Total: ₦{get_total()}")

    elif text == "/today":
        send_message(chat_id, f"Today: ₦{get_today_total()}")

    elif text == "/stats":
        total = get_total()
        today = get_today_total()
        count = get_count()
        top_sender, top_amount = get_top_sender()

        send_message(chat_id,
            f"Total: ₦{total}\nToday: ₦{today}\nCount: {count}\nTop: {top_sender} ({top_amount})"
        )

    elif text == "/history":
        email = get_email_by_chat(chat_id)

        if not email:
            send_message(chat_id, "❌ Link your email first using /link")
        else:
            history = get_user_history(email)

            if not history:
                send_message(chat_id, "No payment history found.")
            else:
                msg_out = "🧾 Last Payments:\n\n"
                for i, (amount, created_at) in enumerate(history, 1):
                    msg_out += f"{i}. ₦{amount} — {created_at[:10]}\n"

                send_message(chat_id, msg_out)

    elif is_payment_message(text):
        amount = extract_amount(text)
        save_payment(amount, text, sender=username)

        send_message(chat_id, f"Payment detected: ₦{amount}")

        if OWNER_CHAT_ID:
            send_message(OWNER_CHAT_ID, f"PAYMENT: ₦{amount}\n{text}")

    else:
        send_message(chat_id, text)

    return "ok", 200


@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    try:
        secret = os.environ.get("PAYSTACK_SECRET_KEY")

        signature = request.headers.get("x-paystack-signature")
        payload = request.data

        computed = hmac.new(secret.encode(), payload, hashlib.sha512).hexdigest()

        if signature != computed:
            return "unauthorized", 401

        data = request.get_json()
        info = data.get("data", {})

        email = info.get("customer", {}).get("email", "").strip().lower()
        amount = info.get("amount", 0) / 100
        ref = info.get("reference")

        save_payment(amount, "PAYSTACK", sender=email, reference=ref)

        user_chat = get_user_by_email(email)

        msg = f"💰 PAYMENT RECEIVED\n₦{amount}\n{email}\n{ref}"

        if user_chat:
            send_message(user_chat, msg)
        elif OWNER_CHAT_ID:
            send_message(OWNER_CHAT_ID, msg)

        return "ok", 200

    except Exception as e:
        print("Paystack error:", e)
        return "error", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
