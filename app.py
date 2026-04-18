from flask import Flask, request
import requests
import os
import hashlib
import hmac

from core.rules import is_payment_message, extract_amount
from config import OWNER_CHAT_ID, TELEGRAM_API

from database.db import (
    # Core
    init_db,
    save_payment,

    # Global stats
    get_total,
    get_today_total,
    get_count,
    get_top_sender,

    # User mapping
    save_user,
    update_user_email,
    get_user_by_email,
    get_email_by_chat,

    # User stats
    get_user_total,
    get_user_today,
    get_user_last,
    get_user_history
)

app = Flask(__name__)

# Initialize DB
init_db()


# -----------------------
# SEND TELEGRAM MESSAGE
# -----------------------
def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Send error:", e)


# -----------------------
# HOME
# -----------------------
@app.route("/", methods=["GET"])
def home():
    return "CashBridgeBot is running"


# -----------------------
# TELEGRAM WEBHOOK
# -----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        if not data:
            return "no data", 200

        print("Incoming:", data)

        if "message" in data:
            msg = data["message"]

            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()
            username = msg.get("chat", {}).get("username", "unknown")

            # -----------------------
            # BASIC COMMANDS
            # -----------------------
            if text == "/start":
                send_message(chat_id, "Bot is alive")

            elif text == "/total":
                send_message(chat_id, f"Total: ₦{int(get_total())}")

            elif text == "/today":
                send_message(chat_id, f"Today: ₦{int(get_today_total())}")

            elif text == "/stats":
                total = int(get_total())
                today = int(get_today_total())
                count = get_count()
                top_sender, top_amount = get_top_sender()

                send_message(
                    chat_id,
                    f"Total: ₦{total}\nToday: ₦{today}\nCount: {count}\nTop: {top_sender} ({int(top_amount)})"
                )

            # -----------------------
            # HISTORY (FIXED POSITION)
            # -----------------------
            elif text == "/history":
                email = get_email_by_chat(chat_id)

                if email:
                    history = get_user_history(email)

                    if history:
                        msg = "🧾 Last Payments:\n\n"

                        for i, (amount, created_at) in enumerate(history, 1):
                            msg += f"{i}. ₦{int(amount)} — {created_at[:10]}\n"

                        send_message(chat_id, msg)
                    else:
                        send_message(chat_id, "No payment history found.")
                else:
                    send_message(chat_id, "❌ Link your email first using /link")

            # -----------------------
            # LINK EMAIL
            # -----------------------
            elif text.startswith("/link"):
                try:
                    email = text.split(" ", 1)[1].strip().lower()

                    save_user(chat_id, username)
                    update_user_email(chat_id, email)

                    send_message(chat_id, f"✅ Linked to {email}")

                except:
                    send_message(chat_id, "Usage: /link your@email.com")

            # -----------------------
            # USER STATS
            # -----------------------
            elif text == "/my_total":
                email = get_email_by_chat(chat_id)

                if email:
                    total = get_user_total(email)
                    send_message(chat_id, f"💰 Your Total: ₦{int(total)}")
                else:
                    send_message(chat_id, "❌ Link your email first using /link")

            elif text == "/my_today":
                email = get_email_by_chat(chat_id)

                if email:
                    today = get_user_today(email)
                    send_message(chat_id, f"📅 Today: ₦{int(today)}")
                else:
                    send_message(chat_id, "❌ Link your email first using /link")

            elif text == "/my_last":
                email = get_email_by_chat(chat_id)

                if email:
                    last = get_user_last(email)

                    if last:
                        amount, time, ref = last
                        send_message(
                            chat_id,
                            f"🧾 Last Payment:\n₦{int(amount)}\n{time}\n{ref}"
                        )
                    else:
                        send_message(chat_id, "No payments found.")
                else:
                    send_message(chat_id, "❌ Link your email first using /link")

            # -----------------------
            # TEXT PAYMENT DETECTION
            # -----------------------
            elif is_payment_message(text):
                amount = extract_amount(text)

                save_payment(amount, text, sender=username)

                send_message(chat_id, f"Payment detected: ₦{amount}")

                if OWNER_CHAT_ID:
                    send_message(OWNER_CHAT_ID, f"PAYMENT: ₦{amount}\n{text}")

            # -----------------------
            # DEFAULT
            # -----------------------
            else:
                send_message(chat_id, text)

        return "ok", 200

    except Exception as e:
        print("Webhook error:", e)
        return "error", 200


# -----------------------
# PAYSTACK WEBHOOK
# -----------------------
@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    try:
        secret = os.environ.get("PAYSTACK_SECRET_KEY")

        signature = request.headers.get("x-paystack-signature")
        payload = request.data

        computed_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha512
        ).hexdigest()

        if signature != computed_signature:
            print("Invalid Paystack signature")
            return "unauthorized", 401

        data = request.get_json()
        print("PAYSTACK EVENT:", data)

        if data.get("event") == "charge.success":
            info = data.get("data", {})

            reference = info.get("reference")
            amount = info.get("amount", 0) / 100
            email = info.get("customer", {}).get("email", "unknown").strip().lower()

            message = (
                "💰 NEW PAYMENT RECEIVED\n\n"
                f"Amount: ₦{int(amount)}\n"
                f"Email: {email}\n"
                f"Ref: {reference}"
            )

            user_chat = get_user_by_email(email)

            if user_chat:
                send_message(user_chat, message)
            elif OWNER_CHAT_ID:
                send_message(OWNER_CHAT_ID, message)

            save_payment(
                amount,
                message,
                sender=email,
                reference=reference
            )

        return "ok", 200

    except Exception as e:
        print("Paystack webhook error:", e)
        return "error", 200


# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
