import sqlite3
from datetime import datetime

DB_NAME = "payments.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL,
        sender TEXT,
        chat_id INTEGER,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_payment(amount, sender, chat_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO payments (amount, sender, chat_id, timestamp)
    VALUES (?, ?, ?, ?)
    """, (amount, sender, chat_id, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_total():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT SUM(amount) FROM payments")
    result = cur.fetchone()[0]

    conn.close()
    return result or 0


def get_today_total():
    today = datetime.now().date().isoformat()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    SELECT SUM(amount) FROM payments
    WHERE DATE(timestamp) = ?
    """, (today,))

    result = cur.fetchone()[0]
    conn.close()

    return result or 0


def get_count():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM payments")
    result = cur.fetchone()[0]

    conn.close()
    return result


def get_top_sender():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    SELECT sender, SUM(amount) as total
    FROM payments
    GROUP BY sender
    ORDER BY total DESC
    LIMIT 1
    """)

    result = cur.fetchone()
    conn.close()

    return result if result else ("None", 0)
