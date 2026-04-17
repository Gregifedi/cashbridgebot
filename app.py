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
    get_top_sender
)

app = Flask(__name__)

init_db()


def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}

        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Send error:", e)


@app.route("/")
def home():
    return "CashBridgeBot is running"


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
            text = msg.get("text", "")
            sender = msg.get("chat", {}).get("username", "unknown")

            if text == "/start":
                send_message(chat_id, "Bot is alive")

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

            elif is_payment_message(text):
                amount = extract_amount(text)

                save_payment(amount, text, sender)

                send_message(chat_id, f"Payment detected: ₦{amount}")

                if OWNER_CHAT_ID:
                    send_message(OWNER_CHAT_ID, f"PAYMENT: ₦{amount}\n{text}")

            else:
                send_message(chat_id, text)

        return "ok", 200

    except Exception as e:
        print("Webhook error:", e)
        return "error", 200


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

        # Reject fake requests
        if signature != computed_signature:
            print("Invalid Paystack signature")
            return "unauthorized", 401

        data = request.get_json()

        print("PAYSTACK EVENT:", data)

        if data.get("event") == "charge.success":
            payload = data.get("data", {})

            reference = payload.get("reference")
            amount = payload.get("amount", 0) / 100
            email = payload.get("customer", {}).get("email", "unknown")

            message = f"""💰 NEW PAYMENT RECEIVED

Amount: ₦{amount}
Email: {email}
Ref: {reference}
"""

            if OWNER_CHAT_ID:
                send_message(OWNER_CHAT_ID, message)

            save_payment(amount, message, sender=email)

        return "ok", 200

    except Exception as e:
        print("Paystack webhook error:", e)
        return "error", 200
        if data.get("event") == "charge.success":
            payload = data["data"]

            amount = payload.get("amount", 0) / 100
            email = payload.get("customer", {}).get("email", "unknown")
            ref = payload.get("reference", "no-ref")

            msg = f"PAYSTACK PAYMENT\n₦{amount}\n{email}\n{ref}"

            if OWNER_CHAT_ID:
                send_message(OWNER_CHAT_ID, msg)

            save_payment(
    amount,
    message,
    sender=email,
    reference=reference
)

        return "ok", 200

    except Exception as e:
        print("Paystack error:", e)
        return "error", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
