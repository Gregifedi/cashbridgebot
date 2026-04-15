import sqlite3
from datetime import datetime, date

DB_PATH = "database/payments.db"


# -----------------------
# INIT DB
# -----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER,
            message TEXT,
            sender TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# -----------------------
# SAVE PAYMENT
# -----------------------
def save_payment(amount, message, sender="unknown"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # safe conversion
    try:
        clean_amount = int(amount)
    except:
        clean_amount = None

    cursor.execute("""
        INSERT INTO payments (amount, message, sender, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        clean_amount,
        message,
        sender,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


# -----------------------
# TOTAL (ALL TIME)
# -----------------------
def get_total():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE amount IS NOT NULL
    """)

    total = cursor.fetchone()[0]
    conn.close()
    return total


# -----------------------
# TODAY TOTAL
# -----------------------
def get_today_total():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE amount IS NOT NULL
        AND DATE(created_at) = ?
    """, (today,))

    total = cursor.fetchone()[0]
    conn.close()
    return total


# -----------------------
# COUNT ALL PAYMENTS
# -----------------------
def get_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM payments
        WHERE amount IS NOT NULL
    """)

    count = cursor.fetchone()[0]
    conn.close()
    return count


# -----------------------
# TOP SENDER
# -----------------------
def get_top_sender():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sender, SUM(amount) as total
        FROM payments
        WHERE amount IS NOT NULL
        GROUP BY sender
        ORDER BY total DESC
        LIMIT 1
    """)

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0], result[1]

    return None, 0
