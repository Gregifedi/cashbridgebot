












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
            amount REAL,
            message TEXT,
            sender TEXT,
            reference TEXT UNIQUE,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE,
            username TEXT,
            email TEXT UNIQUE
        )
    """)

    conn.commit()
    conn.close()


# -----------------------
# SAVE PAYMENT
# -----------------------
def save_payment(amount, message, sender="unknown", reference=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        amount = float(amount) if amount is not None else 0.0
        sender = (sender or "unknown").strip().lower()

        cursor.execute("""
            INSERT INTO payments (amount, message, sender, reference, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            amount,
            message,
            sender,
            reference,
            datetime.utcnow().isoformat()
        ))

        conn.commit()

    except sqlite3.IntegrityError:
        print("Duplicate payment ignored:", reference)

    except Exception as e:
        print("DB INSERT ERROR:", e)

    finally:
        conn.close()


# -----------------------
# USER SAVE / LINK
# -----------------------
def save_user(chat_id, username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO users (chat_id, username)
            VALUES (?, ?)
        """, (chat_id, username))

        conn.commit()

    finally:
        conn.close()


def update_user_email(chat_id, email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = (email or "").strip().lower()

    cursor.execute("""
        INSERT INTO users (chat_id, email)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET email=excluded.email
    """, (chat_id, email))

    conn.commit()
    conn.close()


def get_email_by_chat(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT email FROM users WHERE chat_id = ?
    """, (chat_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = (email or "").strip().lower()

    cursor.execute("""
        SELECT chat_id FROM users WHERE LOWER(email) = ?
    """, (email,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


# -----------------------
# GLOBAL STATS
# -----------------------
def get_total():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE amount IS NOT NULL")
    total = cursor.fetchone()[0]

    conn.close()
    return total


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
    return total


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
        SELECT sender, COALESCE(SUM(amount),0) as total
        FROM payments
        GROUP BY sender
        ORDER BY total DESC
        LIMIT 1
    """)

    result = cursor.fetchone()
    conn.close()

    return result if result else (None, 0)


# -----------------------
# USER STATS
# -----------------------
def get_user_total(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = (email or "").strip().lower()

    cursor.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM payments
        WHERE LOWER(sender)=LOWER(?)
    """, (email,))

    total = cursor.fetchone()[0]
    conn.close()
    return total


def get_user_today(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = (email or "").strip().lower()
    today = date.today().isoformat()

    cursor.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM payments
        WHERE LOWER(sender)=LOWER(?)
        AND DATE(created_at)=?
    """, (email, today))

    total = cursor.fetchone()[0]
    conn.close()
    return total


def get_user_last(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = (email or "").strip().lower()

    cursor.execute("""
        SELECT amount, created_at, reference
        FROM payments
        WHERE LOWER(sender)=LOWER(?)
        ORDER BY id DESC
        LIMIT 1
    """, (email,))

    result = cursor.fetchone()
    conn.close()
    return result


def get_user_history(email, limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = (email or "").strip().lower()

    cursor.execute("""
        SELECT amount, created_at
        FROM payments
        WHERE LOWER(sender)=LOWER(?)
        ORDER BY id DESC
        LIMIT ?
    """, (email, limit))

    rows = cursor.fetchall()
    conn.close()

    return rows
