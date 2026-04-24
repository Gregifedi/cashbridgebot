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
    get_user_history
)

app = Flask(__name__)
init_db()


# -----------------------
# TELEGRAM SEND
# -----------------------
def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
    except Exception as e:
        print("Send error:", e)


# -----------------------
# HOME
# -----------------------
@app.route("/")
def home():
    return "CashBridgeBot is running"


# -----------------------
# WEBHOOK
# -----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return "ok", 200

        msg = data["message"]

        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()

        user = msg.get("from", {})
        username = user.get("username") or user.get("first_name") or str(chat_id)

        # ---------------- COMMANDS ----------------

        if text == "/start":
            send_message(chat_id, "Bot is alive")

        elif text == "/pay":
            send_message(
                chat_id,
                "💳 Premium Access\n\n"
                "Get access to the private group for just ₦1,000\n\n"
                "📌 What you’ll get:\n"
                "- Real money tips\n"
                "- Useful tools\n"
                "- Daily updates\n\n"
                "━━━━━━━━━━━━━━━\n"
                "💰 Payment Details:\n"
                "Bank: First Bank\n"
                "Account Name: Osakwe Gregory Ifedi\n"
                "Account Number: 3098765431\n"
                "━━━━━━━━━━━━━━━\n\n"
                "After payment, send:\n"
                "I paid 1000\n\n"
                "⚡ You’ll be added immediately.\n"
                "⚠️ Limited slots — price may increase soon"
            )

        elif text.startswith("/link"):
            parts = text.split(" ", 1)

            if len(parts) < 2:
                send_message(chat_id, "Usage: /link email@example.com")
            else:
                email = parts[1].strip().lower()
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
            top = get_top_sender() or ("None", 0)

            send_message(
                chat_id,
                f"Total: ₦{total}\nToday: ₦{today}\nCount: {count}\nTop: {top[0]} ({top[1]})"
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

        # ---------------- PAYMENT DETECTION ----------------

        elif is_payment_message(text):
            amount = extract_amount(text)

            save_payment(
                amount=amount,
                message=text,
                sender=username
            )

            send_message(
                chat_id,
                f"✅ Payment received: ₦{amount}\n\n"
                "⏳ Processing your access...\n"
                "You’ll be added shortly."
            )

            if OWNER_CHAT_ID:
                send_message(
                    OWNER_CHAT_ID,
                    f"💰 NEW PAYMENT\n\n₦{amount}\nUser: {username}\nChat ID: {chat_id}"
                )

        else:
            send_message(chat_id, text)

        return "ok", 200

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "error", 200


# -----------------------
# PAYSTACK WEBHOOK
# -----------------------
@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    try:
        secret = os.environ.get("PAYSTACK_SECRET_KEY")
        signature = request.headers.get("x-paystack-signature")

        if not secret or not signature:
            return "unauthorized", 401

        payload = request.data
        computed = hmac.new(secret.encode(), payload, hashlib.sha512).hexdigest()

        if signature != computed:
            return "unauthorized", 401

        data = request.get_json() or {}
        info = data.get("data", {})

        email = info.get("customer", {}).get("email", "").strip().lower()
        amount = (info.get("amount") or 0) / 100
        ref = info.get("reference")

        if not email:
            return "ok", 200

        chat_id = get_user_by_email(email)

        save_payment(
            amount=amount,
            message="PAYSTACK",
            sender=email
        )

        msg = f"💰 PAYMENT RECEIVED\n₦{amount}\n{email}\n{ref}"

        if chat_id:
            send_message(chat_id, msg)
        elif OWNER_CHAT_ID:
            send_message(OWNER_CHAT_ID, msg)

        return "ok", 200

    except Exception as e:
        print("Paystack error:", e)
        return "error", 200


# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
