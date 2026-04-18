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
        amount = float(amount) if amount is not None else None

        cursor.execute("""
            INSERT INTO payments (amount, message, sender, reference, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            amount,
            message,
            sender.lower(),
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
# SAVE USER
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

    except Exception as e:
        print("SAVE USER ERROR:", e)

    finally:
        conn.close()


# -----------------------
# UPDATE USER EMAIL
# -----------------------
def update_user_email(chat_id, email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = email.strip().lower()

    cursor.execute("""
        UPDATE users
        SET email = ?
        WHERE chat_id = ?
    """, (email, chat_id))

    conn.commit()
    conn.close()


# -----------------------
# GET CHAT BY EMAIL
# -----------------------
def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = email.strip().lower()

    cursor.execute("""
        SELECT chat_id FROM users WHERE LOWER(email) = ?
    """, (email,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


# -----------------------
# GET EMAIL BY CHAT
# -----------------------
def get_email_by_chat(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT email FROM users WHERE chat_id = ?
    """, (chat_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


# -----------------------
# TOTAL (ALL)
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
# COUNT
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
        SELECT sender, SUM(amount)
        FROM payments
        WHERE amount IS NOT NULL
        GROUP BY sender
        ORDER BY SUM(amount) DESC
        LIMIT 1
    """)

    result = cursor.fetchone()
    conn.close()

    return result if result else (None, 0)


# -----------------------
# USER TOTAL
# -----------------------
def get_user_total(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE LOWER(sender) = LOWER(?)
    """, (email,))

    total = cursor.fetchone()[0]
    conn.close()
    return total


# -----------------------
# USER TODAY
# -----------------------
def get_user_today(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE LOWER(sender) = LOWER(?)
        AND DATE(created_at) = ?
    """, (email, today))

    total = cursor.fetchone()[0]
    conn.close()
    return total


# -----------------------
# USER LAST
# -----------------------
def get_user_last(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT amount, created_at, reference
        FROM payments
        WHERE LOWER(sender) = LOWER(?)
        ORDER BY id DESC
        LIMIT 1
    """, (email,))

    result = cursor.fetchone()
    conn.close()
    return result	

# -----------------------
# USER PAYMENT HISTORY
# -----------------------
def get_user_history(email, limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT amount, created_at
        FROM payments
        WHERE LOWER(sender) = LOWER(?)
        ORDER BY id DESC
        LIMIT ?
    """, (email, limit))

    results = cursor.fetchall()
    conn.close()
