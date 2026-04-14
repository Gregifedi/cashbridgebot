import re

def is_payment_message(text):
    text = text.lower()

    keywords = [
        "credited",
        "credit alert",
        "debit alert",
        "received",
        "transfer",
        "payment",
        "deposit"
    ]

    return any(word in text for word in keywords)


def extract_amount(text):
    """
    Extracts amount like ₦5000, N5000, 5000 NGN, etc.
    Returns int or None
    """

    # match ₦5000 or N5000 or 5000
    patterns = [
        r"₦\s?([\d,]+)",
        r"\bN\s?([\d,]+)",
        r"\b([\d,]+)\s?naira",
        r"\b([\d,]{3,})\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except:
                pass

    return None
