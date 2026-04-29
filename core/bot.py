from database import db
import random
import string

def generate_referral_code():
    """Generate a random 6-character referral code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


@bot.message_handler(commands=['referral'])
def referral_handler(message):
    chat_id = str(message.chat.id)

    # Ensure user exists in DB
    db.save_user(chat_id, message.from_user.username)

    # Get referral code
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT referral_code FROM users WHERE chat_id=?", (chat_id,))
    result = cursor.fetchone()
    referral_code = result[0] if result and result[0] else None

    # If no code yet, generate one
    if not referral_code:
        referral_code = generate_referral_code()
        cursor.execute("UPDATE users SET referral_code=? WHERE chat_id=?", (referral_code, chat_id))
        conn.commit()
    conn.close()

    # Get referral stats
    count = db.get_referral_stats(chat_id)

    # Build referral link
    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"

    # Reply to user
    bot.send_message(
        chat_id,
        f"🔗 Your referral link:\n{referral_link}\n\n"
        f"👥 Referrals: {count} / 3\n"
        f"💰 Reward: {'₦2000 credited!' if count >= 3 else '₦0'}\n\n"
        f"Invite {max(0, 3-count)} more to earn ₦2000!"
    )
