import re

KEYWORDS = [
    "credited",
    "credit alert",
    "debit alert",
    "received",
    "transfer",
    "payment",
    "deposit",
    "paid",
    "sent"
]


def is_payment_message(text):
    if not text:
        return False

    text = text.lower()

    has_keyword = any(k in text for k in KEYWORDS)
    has_number = re.search(r"\d+", text) is not None

    return has_keyword and has_number


def extract_amount(text):
    if not text:
        return 0.0

    text = text.replace(",", "")

    match = re.search(r"(\d+)", text)
    return float(match.group(1)) if match else 0.0
