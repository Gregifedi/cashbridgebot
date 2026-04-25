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

    text = text.replace(",", "").lower()

    patterns = [
        r"₦\s?(\d+)",
        r"\bngn\s?(\d+)",
        r"\bn\s?(\d+)",
        r"(\d+)"
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return float(m.group(1))

    return 0.0
