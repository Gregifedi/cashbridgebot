import re

def is_payment_message(text):
    if not text:
        return False

    text = text.lower()

    keywords = [
        "credited",
        "credit alert",
        "debit alert",
        "received",
        "transfer",
        "payment",
        "deposit",
        "paid",     # important for your flow
        "sent"      # extra coverage
    ]

    # must contain keyword AND a number
    has_keyword = any(word in text for word in keywords)
    has_amount = re.search(r'\d+', text)

    return has_keyword and has_amount


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

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))

    return 0.0
