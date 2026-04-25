import re


def is_payment_message(text):
    if not text:
        return False

    keywords = ["credit", "alert", "received", "payment", "deposit"]
    text = text.lower()

    return any(word in text for word in keywords)


def extract_amount(text):
    if not text:
        return 0

    # Matches formats like 5000, 5,000, 5000.00
    match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', text)

    if match:
        amount = match.group(1).replace(",", "")
        return float(amount)

    return 0


def extract_sender(text):
    if not text:
        return "Unknown"

    # VERY basic sender extraction (you can improve later)
    match = re.search(r'from\s+([A-Za-z ]+)', text, re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return "Unknown"
