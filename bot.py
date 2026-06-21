---

# 1) فولدەرەکان دروست بکە

```bash  
ultimate_bot  
ultimate_bot/handlers  
ultimate_bot/utils  
ultimate_bot/data  
```

---

# 2) `requirements.txt`
```txt  
python-telegram-bot==20.7  
python-dotenv==1.0.1  
```

---

# 3) `.env`
```env    8759839149:AAFvqz5q-DuQhXr0xUxR4Pf9Xe82BniH274
ADMIN_ID=7643191802  
CHANNEL_USERNAME=@eyeofiraq_bot  
```

---

# 4) `.gitignore`
```gitignore  
.env  
__pycache__/
data/bot.db  
data/users.csv  
data/bot.log  
```

---

# 5) `config.py`
```python  
import os  
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("8759839149:AAFvqz5q-DuQhXr0xUxR4Pf9Xe82BniH274")
ADMIN_ID = int(os.getenv("7643191802", "0"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@eyeofiraq_bot")

DB_PATH = "data/bot.db"
CSV_PATH = "data/users.csv"
LOG_PATH = "data/bot.log"
```

---

# 6) `database.py`
```python  
import os  
import sqlite3  
from config import DB_PATH

os.makedirs("data", exist_ok=True)

def connect():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            language TEXT DEFAULT 'ku',
            points INTEGER DEFAULT 0,
            ref_by INTEGER,
            is_banned INTEGER DEFAULT 0,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT,
            amount INTEGER,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
        )
    """)

    conn.commit()
    conn.close()

def save_user(user, ref_by=None):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user.id,))
    exists = cur.fetchone()

    if not exists:
        cur.execute("""
            INSERT INTO users (user_id, first_name, username, ref_by)
            VALUES (?, ?, ?, ?)
        """, (user.id, user.first_name, user.username, ref_by))

    conn.commit()
    conn.close()

def add_points(user_id, points):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

def get_points(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

def set_language(user_id, lang):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def get_language(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "ku"

def save_feedback(user_id, message):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO feedback (user_id, message) VALUES (?, ?)", (user_id, message))
    conn.commit()
    conn.close()

def create_order(user_id, product_name, amount):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (user_id, product_name, amount)
        VALUES (?, ?, ?)
    """, (user_id, product_name, amount))
    conn.commit()
    conn.close()

def get_all_orders():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, product_name, amount, status, created_at  
        FROM orders  
        ORDER BY id DESC  
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_count():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE is_banned = 0")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_all_user_rows():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, first_name, username, language, points, is_banned, joined_at  
        FROM users  
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def ban_user(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row and row[0] == 1)
```

---

# 7) `bot.py`
```python  
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN  
from database import init_db  
from handlers.start import start_command, help_command  
from handlers.user import (
    profile_command,
    id_command,
    points_command,
    language_command,
    feedback_command,
    text_handler,
)
from handlers.store import order_command  
from handlers.admin import (
    stats_command,
    broadcast_command,
    ban_command,
    unban_command,
    export_command,
    orders_command,
)
from handlers.callbacks import button_callback  
from handlers.media import photo_handler, document_handler

async def error_handler(update, context):
    print("Error:", context.error)

def main():
    init_db()

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("points", points_command))
    app.add_handler(CommandHandler("lang", language_command))
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(CommandHandler("order", order_command))

    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(CommandHandler("orders", orders_command))

    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.add_error_handler(error_handler)

    print("Ultimate Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
```

---

# 8) `handlers/__init__.py`
```python  
# empty  
```

---

# 9) `handlers/start.py`
```python  
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup  
from telegram.ext import ContextTypes  
from database import save_user, add_points, is_banned  
from utils.checks import is_joined_channel  
from config import CHANNEL_USERNAME

menu = ReplyKeyboardMarkup(
    [["help", "profile"], ["id", "points"], ["language", "store"]],
    resize_keyboard=True  
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_banned(user.id):
        await update.message.reply_text("You are banned.")
        return

    joined = await is_joined_channel(context.bot, user.id)
    if not joined:
        keyboard = [
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("Check Again", callback_data="check_join")]
        ]
        await update.message.reply_text(
            "Please join the channel first.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    ref_by = None  
    if context.args:
        try:
            ref_by = int(context.args[0])
        except Exception:
            ref_by = None

    save_user(user, ref_by=ref_by)

    if ref_by and ref_by != user.id:
        add_points(ref_by, 5)

    me = await context.bot.get_me()
    ref_link = f"https://t.me/{me.username}?start={user.id}"

    await update.message.reply_text(
        f"Welcome {user.first_name} ✅\nYour referral link:\n{ref_link}",
        reply_markup=menu  
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start\n"
        "/help\n"
        "/id\n"
        "/profile\n"
        "/points\n"
        "/lang ku|en\n"
        "/feedback your_message\n"
        "/order product amount"
    )
```

---

# 10) `handlers/user.py`
```python  
from telegram import Update  
from telegram.ext import ContextTypes  
from database import get_points, set_language, save_feedback, get_language

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user  
    lang = get_language(user.id)
    username = f"@{user.username}" if user.username else "None"

    await update.message.reply_text(
        f"Name: {user.first_name}\n"
        f"Username: {username}\n"
        f"ID: {user.id}\n"
        f"Language: {lang}"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pts = get_points(update.effective_user.id)
    await update.message.reply_text(f"Points: {pts}")

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /lang ku or /lang en")
        return

    lang = context.args[0].lower()
    if lang not in ["ku", "en"]:
        await update.message.reply_text("Only ku or en")
        return

    set_language(update.effective_user.id, lang)
    await update.message.reply_text(f"Language changed to: {lang}")

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /feedback your_message")
        return

    message = " ".join(context.args)
    save_feedback(update.effective_user.id, message)
    await update.message.reply_text("Feedback saved ✅")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").lower()

    if msg == "help":
        await update.message.reply_text("Use /help")
    elif msg == "profile":
        await profile_command(update, context)
    elif msg == "id":
        await id_command(update, context)
    elif msg == "points":
        await points_command(update, context)
    elif msg == "language":
        await update.message.reply_text("Use: /lang ku or /lang en")
    elif msg == "store":
        await update.message.reply_text("Use: /order product_name amount")
    else:
        await update.message.reply_text(f"You said: {update.message.text}")
```

---

# 11) `handlers/store.py`
```python  
from telegram import Update  
from telegram.ext import ContextTypes  
from database import create_order

async def order_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /order product_name amount")
        return

    product_name = context.args[0]

    try:
        amount = int(context.args[1])
    except Exception:
        await update.message.reply_text("Amount must be a number.")
        return

    create_order(update.effective_user.id, product_name, amount)
    await update.message.reply_text(
        f"Order saved ✅\nProduct: {product_name}\nAmount: {amount}\nPayment: contact admin"
    )
```

---

# 12) `handlers/admin.py`
```python  
from telegram import Update  
from telegram.ext import ContextTypes  
from utils.checks import is_admin  
from database import get_user_count, get_all_users, ban_user, unban_user, get_all_orders  
from utils.export_csv import export_users_to_csv

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not admin.")
        return

    await update.message.reply_text(f"Users: {get_user_count()}")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not admin.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast message")
        return

    text = " ".join(context.args)
    users = get_all_users()
    sent = 0  
    failed = 0

    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
            sent += 1  
        except Exception:
            failed += 1

    await update.message.reply_text(f"Done\nSent: {sent}\nFailed: {failed}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not admin.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /ban user_id")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be a number.")
        return

    ban_user(user_id)
    await update.message.reply_text(f"{user_id} banned")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not admin.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /unban user_id")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be a number.")
        return

    unban_user(user_id)
    await update.message.reply_text(f"{user_id} unbanned")

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not admin.")
        return

    path = export_users_to_csv()
    with open(path, "rb") as f:
        await update.message.reply_document(document=f)

async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not admin.")
        return

    orders = get_all_orders()
    if not orders:
        await update.message.reply_text("No orders.")
        return

    lines = []
    for oid, uid, product, amount, status, created_at in orders[:20]:
        lines.append(f"#{oid} | user:{uid} | {product} | qty:{amount} | {status}")

    await update.message.reply_text("\n".join(lines))
```

---

# 13) `handlers/callbacks.py`
```python  
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  
from telegram.ext import ContextTypes  
from utils.checks import is_joined_channel  
from config import CHANNEL_USERNAME

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query  
    user = query.from_user  
    await query.answer()

    if query.data == "check_join":
        joined = await is_joined_channel(context.bot, user.id)
        if joined:
            await query.message.reply_text("Join confirmed ✅ Send /start")
        else:
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]
            ]
            await query.message.reply_text(
                "You still have not joined.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
```

---

# 14) `handlers/media.py`
```python  
from telegram import Update  
from telegram.ext import ContextTypes

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Photo received ✅")

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Document received ✅")
```

---

# 15) `utils/__init__.py`
```python  
# empty  
```

---

# 16) `utils/checks.py`
```python  
from config import ADMIN_ID, CHANNEL_USERNAME

def is_admin(user_id):
    return user_id == ADMIN_ID

async def is_joined_channel(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME
