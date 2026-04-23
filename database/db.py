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
            chat_id TEXT,
            amount REAL,
            message TEXT,
            sender TEXT,
            reference TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id TEXT PRIMARY KEY,
            username TEXT,
            email TEXT
        )
    """)

    conn.commit()
    conn.close()


# -----------------------
# SAVE PAYMENT (FIXED CORE)
# -----------------------
def save_payment(amount, message, chat_id, sender="unknown", reference=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO payments (chat_id, amount, message, sender, reference, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(chat_id),
            float(amount or 0),
            message,
            sender,
            reference,
            datetime.utcnow().isoformat()
        ))

        conn.commit()

    except Exception as e:
        print("DB ERROR:", e)

    finally:
        conn.close()


# -----------------------
# USERS
# -----------------------
def save_user(chat_id, username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users (chat_id, username)
        VALUES (?, ?)
    """, (str(chat_id), username))

    conn.commit()
    conn.close()


def update_user_email(chat_id, email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (chat_id, email)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET email=excluded.email
    """, (str(chat_id), email.strip().lower()))

    conn.commit()
    conn.close()


def get_email_by_chat(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE chat_id=?", (str(chat_id),))
    row = cursor.fetchone()

    conn.close()
    return row[0] if row else None


def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT chat_id FROM users WHERE email=?", (email.strip().lower(),))
    row = cursor.fetchone()

    conn.close()
    return row[0] if row else None


# -----------------------
# STATS (GLOBAL)
# -----------------------
def get_total():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payments")
    total = cursor.fetchone()[0]

    conn.close()
    return float(total)


def get_today_total():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM payments
        WHERE DATE(created_at)=?
    """, (today,))

    total = cursor.fetchone()[0]
    conn.close()
    return float(total)


def get_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM payments")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_top_sender():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sender, COALESCE(SUM(amount),0)
        FROM payments
        GROUP BY sender
        ORDER BY SUM(amount) DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    return row if row else ("None", 0)


# -----------------------
# HISTORY (FIXED)
# -----------------------
def get_user_history(chat_id, limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT amount, created_at
        FROM payments
        WHERE chat_id=?
        ORDER BY id DESC
        LIMIT ?
    """, (str(chat_id), limit))

    rows = cursor.fetchall()
    conn.close()

    return rows
