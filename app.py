from flask import Flask, request
import requests
import os

from core.rules import is_payment_message, extract_amount
from config import OWNER_CHAT_ID, TELEGRAM_API
from database.db import init_db, save_payment

app = Flask(__name__)

# Initialize DB on startup
init_db()


# -----------------------
# SEND MESSAGE FUNCTION
# -----------------------
def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code != 200:
            print("Telegram API error:", response.text)

    except Exception as e:
        print("Send message error:", e)


# -----------------------
# HOME ROUTE
# -----------------------
@app.route("/", methods=["GET"])
def home():
    return "CashBridgeBot is running"


# -----------------------
# WEBHOOK ROUTE
# -----------------------
@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    try:
        data = request.get_json()

        if not data:
            return "no data", 200

        print("PAYSTACK EVENT:", data)

        event = data.get("event")

        if event == "charge.success":

            payload = data.get("data", {})

            amount = payload.get("amount", 0) / 100
            email = payload.get("customer", {}).get("email", "unknown")
            reference = payload.get("reference", "no-ref")

            message = f"""💰 NEW PAYMENT RECEIVED

Amount: ₦{amount}
Email: {email}
Ref: {reference}
"""

            # Send Telegram alert
            if OWNER_CHAT_ID:
                send_message(OWNER_CHAT_ID, message)

            # Save to database
            save_payment(amount, message, sender=email)

        return "ok", 200

    except Exception as e:
        print("Paystack webhook error:", e)
        return "error", 200
        msg = data["message"]

        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # sender info (safe fallback)
        sender = msg.get("chat", {}).get("username", "unknown")

        # -----------------------
        # START COMMAND
        # -----------------------
        if text == "/start":
            send_message(chat_id, "CashBridgeBot online. Ready.")

        # -----------------------
        # PAYMENT DETECTION
        # -----------------------
        elif is_payment_message(text):

            amount = extract_amount(text)

            # save to database (always save even if amount missing)
            save_payment(amount, text, sender=sender)

            if amount:
                send_message(chat_id, f"💰 Payment detected: ₦{amount}")

                if OWNER_CHAT_ID:
                    send_message(
                        OWNER_CHAT_ID,
                        f"💰 PAYMENT ALERT\nAmount: ₦{amount}\nSender: @{sender}\n\n{text}"
                    )
            else:
                send_message(chat_id, "💰 Payment detected")

                if OWNER_CHAT_ID:
                    send_message(
                        OWNER_CHAT_ID,
                        f"💰 PAYMENT ALERT (NO AMOUNT)\nSender: @{sender}\n\n{text}"
                    )

        # -----------------------
        # NORMAL MESSAGE
        # -----------------------
        else:
            send_message(chat_id, f"You said: {text}")

            if OWNER_CHAT_ID:
                send_message(
                    OWNER_CHAT_ID,
                    f"📩 New message from @{sender}:\n{text}"
                )

        return "ok", 200

    except Exception as e:
        print("Webhook error:", e)
        return "error", 200


# -----------------------
# RUN APP
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)












