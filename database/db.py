import sqlite3
from datetime import datetime

DB_NAME = "database/payments.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount TEXT,
        message TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_payment(amount, message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO payments (amount, message, created_at)
    VALUES (?, ?, ?)
    """, (amount, message, datetime.now().isoformat()))

    conn.commit()
    conn.close()
