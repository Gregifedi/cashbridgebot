import psycopg2
import os
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")


# -----------------------
# CONNECTION
# -----------------------
def get_conn():
    return psycopg2.connect(DATABASE_URL)


# -----------------------
# INIT DB
# -----------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id BIGINT PRIMARY KEY,
        username TEXT,
        email TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT,
        amount NUMERIC,
        message TEXT,
        reference TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# -----------------------
# USER FUNCTIONS
# -----------------------
def save_user(chat_id, username):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (chat_id, username)
        VALUES (%s, %s)
        ON CONFLICT (chat_id)
        DO UPDATE SET username = EXCLUDED.username
    """, (chat_id, username))

    conn.commit()
    conn.close()


def update_user_email(chat_id, email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users SET email = %s WHERE chat_id = %s
    """, (email, chat_id))

    conn.commit()
    conn.close()


def get_email_by_chat(chat_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT email FROM users WHERE chat_id = %s", (chat_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else None


def get_user_by_email(email):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT chat_id FROM users WHERE email = %s", (email,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else None


# -----------------------
# PAYMENT FUNCTIONS
# -----------------------
def save_payment(amount, message, sender=None, reference=None, chat_id=None):
    """
    We prioritize chat_id as identity.
    If not available, fallback to lookup by sender email.
    """

    conn = get_conn()
    cur = conn.cursor()

    resolved_chat_id = chat_id

    # if chat_id not provided, try resolve via email
    if not resolved_chat_id and sender:
        cur.execute("SELECT chat_id FROM users WHERE email = %s", (sender,))
        row = cur.fetchone()
        if row:
            resolved_chat_id = row[0]

    cur.execute("""
        INSERT INTO payments (chat_id, amount, message, reference)
        VALUES (%s, %s, %s, %s)
    """, (resolved_chat_id, amount, message, reference))

    conn.commit()
    conn.close()


# -----------------------
# STATS
# -----------------------
def get_total():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM payments")
    total = cur.fetchone()[0]

    conn.close()
    return float(total)


def get_today_total():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM payments
        WHERE DATE(created_at) = CURRENT_DATE
    """)

    total = cur.fetchone()[0]
    conn.close()
    return float(total)


def get_count():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM payments")
    count = cur.fetchone()[0]

    conn.close()
    return count


def get_top_sender():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT u.email, COALESCE(SUM(p.amount),0) as total
        FROM payments p
        LEFT JOIN users u ON p.chat_id = u.chat_id
        GROUP BY u.email
        ORDER BY total DESC
        LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return ("None", 0)

    return row[0], float(row[1])


def get_user_history(email, limit=10):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.amount, p.created_at
        FROM payments p
        JOIN users u ON p.chat_id = u.chat_id
        WHERE u.email = %s
        ORDER BY p.created_at DESC
        LIMIT %s
    """, (email, limit))

    rows = cur.fetchall()
    conn.close()

    return rows
