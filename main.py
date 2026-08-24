import os
import re
import sqlite3
import random
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.error import RetryAfter

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8871976724:AAHM7zr9ertWF3bbn6X8pyrd739p9tXLB74"  # আপনার বট টোকেন দিন
ADMIN_ID = 5747820322              # আপনার টেলিগ্রাম ID (Integer)
MUST_JOIN_CHANNEL = "@Crypto_Royels" # ডিরেক্ট ইউজারদের যে চ্যানেলে জয়েন করাতে চান
SUPPORT_LINK = "t.me/Crypto_Tanvir"
OTP_GROUP_LINK = "https://t.me/+MbuMh29hodEyOTE1"

BINANCE_PAY_ID = "996941749 (Binance Pay ID)"
BITGET_PAY_ID = "0xfda41136ed44aebd172f92b63a60d3b0defee83d / Address"

# ==================== WEB SERVER FOR UPTIMEROBOT ====================
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ==================== DATABASE SETUP ====================
DB_NAME = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        username TEXT,
        sub_plan TEXT DEFAULT 'None',
        sub_end_date TEXT DEFAULT NULL
    )''')
    
    # Countries Table
    c.execute('''CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        flag TEXT,
        service TEXT,
        is_hidden INTEGER DEFAULT 0
    )''')

    # Stock Numbers Table
    c.execute('''CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_name TEXT,
        number TEXT
    )''')

    # System Settings Table (Traffic Text, etc.)
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # Insert Default Traffic if not exists
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('live_traffic', '🔥 30 Minute LIVE Traffic\n\n📱 FACEBOOK 1\n🇲🇬 MADAGASCAR : HIGH 🟢\n🇺🇦 UKRAINE : HIGH 🟢\n\n📱 WHATSAPP 1\n🇲🇬 MADAGASCAR : HIGH 🟢')")
    
    # Insert Default Countries
    default_countries = [
        ('Bangladesh', '🇧🇩', 'WS', 0),
        ('Togo', '🇹🇬', 'TG', 0),
        ('Sierra Leone', '🇸🇱', 'TG', 0),
        ('Ukraine', '🇺🇦', 'WS', 0),
        ('Madagascar', '🇲🇬', 'WS', 0)
    ]
    for c_name, c_flag, c_srv, c_hid in default_countries:
        c.execute("INSERT OR IGNORE INTO countries (name, flag, service, is_hidden) VALUES (?, ?, ?, ?)", (c_name, c_flag, c_srv, c_hid))
        
    conn.commit()
    conn.close()

init_db()

# Global State Dictionary
user_states = {}
active_tasks = {}

# ==================== HELPER FUNCTIONS ====================
def get_db():
    return sqlite3.connect(DB_NAME)

def is_subscribed(user_id):
    if user_id == ADMIN_ID:
        return True
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT sub_end_date FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    if res and res[0]:
        end_dt = datetime.strptime(res[0], "%Y-%m-%d %H:%M:%S")
        if end_dt > datetime.now():
            return True
    return False

# ==================== MAIN HANDLERS ====================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, full_name, username) VALUES (?, ?, ?)",
              (user.id, user.full_name, user.username or ""))
    conn.commit()
    conn.close()

    # Force Join Check
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{MUST_JOIN_CHANNEL.replace('@','')}")],
        [InlineKeyboardButton("✅ Verify Join", callback_data="verify_join")]
    ])
    await update.message.reply_text(
        f"👋 Hi {user.full_name}!\n\n⚠️ You must join our official channel to use this bot.",
        reply_markup=keyboard
    )

async def send_main_menu(chat_id, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Get Number", callback_data="get_number"), InlineKeyboardButton("🔥 Live Traffic", callback_data="live_traffic")],
        [InlineKeyboardButton("📊 My Stats", callback_data="my_stats"), InlineKeyboardButton("📢 Support", url=SUPPORT_LINK)]
    ])
    await context.bot.send_message(
        chat_id=chat_id,
        text="✨ **Welcome to Secret OTP Bot Main Menu** ✨\nSelect an option below:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "verify_join":
        await query.answer("Verified! Welcome.")
        await send_main_menu(query.message.chat_id, context)

    elif data == "my_stats":
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT full_name, username, sub_plan, sub_end_date FROM users WHERE user_id=?", (user_id,))
        res = c.fetchone()
        conn.close()
        
        plan = res[2] if res else "None"
        exp = res[3] if res and res[3] else "No Active Plan"
        
        msg = (
            f"👤 **User Stats**\n\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"📛 **Name:** {query.from_user.full_name}\n"
            f"🏷️ **Username:** @{query.from_user.username or 'N/A'}\n"
            f"💳 **Subscription Plan:** {plan}\n"
            f"⏳ **Expires On:** `{exp}`"
        )
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif data == "live_traffic":
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key='live_traffic'")
        traffic = c.fetchone()[0]
        conn.close()
        await query.message.reply_text(traffic)

    elif data == "get_number":
        if not is_subscribed(user_id):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💸 Get Subscription", callback_data="buy_sub")]
            ])
            await query.message.reply_text("❌ **No Active Subscription.**", reply_markup=keyboard, parse_mode="Markdown")
        else:
            # Show Countries
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, name, flag FROM countries WHERE is_hidden=0")
            countries = c.fetchall()
            conn.close()

            buttons = []
            for cid, cname, cflag in countries:
                buttons.append(InlineKeyboardButton(f"{cflag} {cname}", callback_data=f"cnum_{cid}"))
            
            # Split into pairs of 2
            pair_buttons = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
            await query.message.reply_text("📱 **Select a Country:**", reply_markup=InlineKeyboardMarkup(pair_buttons), parse_mode="Markdown")

    elif data.startswith("cnum_"):
        cid = int(data.split("_")[1])
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT name, flag, service FROM countries WHERE id=?", (cid,))
        country = c.fetchone()
        
        # Get 4 Stock Numbers
        c.execute("SELECT number FROM stock WHERE country_name=? LIMIT 4", (country[0],))
        numbers = c.fetchall()
        conn.close()

        num_text = ""
        if numbers:
            for n in numbers:
                num_text += f"• `{n[0]}`\n"
        else:
            num_text = f"• `{country[1]} 88017{random.randint(100000,999999)}`\n• `{country[1]} 88018{random.randint(100000,999999)}`\n"

        srv_logo = "💬 WhatsApp" if country[2] == "WS" else "✈️ Telegram"
        
        msg = (
            f"🌐 **Country:** {country[1]} {country[0]} ({srv_logo})\n\n"
            f"📱 **Available Stock Numbers:**\n{num_text}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Stock", callback_data=f"cnum_{cid}")],
            [InlineKeyboardButton("📩 Live OTP Group", url=OTP_GROUP_LINK)]
        ])
        await query.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")

    elif data == "buy_sub":
        msg = (
            "💳 **Subscription Packages:**\n\n"
            "1️⃣ 1 Month - $2\n"
            "2️⃣ 3 Months - $5\n"
            "3️⃣ 6 Months - $10\n\n"
            "📌 **Payment Details:**\n"
            f"🔸 **Binance Pay ID:** `{BINANCE_PAY_ID}`\n"
            f"🔸 **Bitget Pay ID:** `{BITGET_PAY_ID}`\n\n"
            "Send payment and click **'Submit Payment Proof'** below."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Submit Payment Proof", callback_data="submit_pay")]
        ])
        await query.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")

    elif data == "submit_pay":
        user_states[user_id] = "WAITING_PAYMENT_PROOF"
        await query.message.reply_text("✍️ Please type your **Transaction TRX ID** or **Order ID**:")

    elif data.startswith("copy_"):
        code = data.split("_")[1]
        await query.answer(text=f"🔑 Copied OTP Code: {code}", show_alert=True)

    # ADMIN CALLBACKS
    elif data.startswith("adm_approve_"):
        target_uid = int(data.split("_")[2])
        # Default 1 Month Add
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET sub_plan='1 Month', sub_end_date=? WHERE user_id=?", (end_date, target_uid))
        conn.commit()
        conn.close()
        
        await query.message.edit_text(f"✅ Approved Subscription for User ID: `{target_uid}`")
        await context.bot.send_message(chat_id=target_uid, text="🎉 **Your Subscription has been Approved by Admin!**")

    elif data.startswith("adm_toggle_"):
        cid = int(data.split("_")[2])
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE countries SET is_hidden = 1 - is_hidden WHERE id=?", (cid,))
        conn.commit()
        conn.close()
        await query.answer("Country Hide/Unhide Status Changed!")
        await admin_manage_countries(query.message, context)

# ==================== ADMIN PANEL COMMANDS ====================
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Hide / Unhide Countries", callback_data="adm_countries")],
        [InlineKeyboardButton("📦 Upload Stock File", callback_data="adm_stock"), InlineKeyboardButton("📝 Edit Live Traffic", callback_data="adm_traffic")],
        [InlineKeyboardButton("📢 Broadcast to All Users", callback_data="adm_broadcast")]
    ])
    await update.message.reply_text("👑 **Admin Control Panel** 👑", reply_markup=keyboard)

async def admin_manage_countries(message, context):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, flag, is_hidden FROM countries")
    rows = c.fetchall()
    conn.close()
    
    buttons = []
    for cid, cname, cflag, chid in rows:
        status = "🔴 Hidden" if chid == 1 else "🟢 Active"
        buttons.append([InlineKeyboardButton(f"{cflag} {cname} [{status}]", callback_data=f"adm_toggle_{cid}")])
    
    await message.reply_text("⚙️ **Click to Toggle Hide/Unhide:**", reply_markup=InlineKeyboardMarkup(buttons))

# ==================== BROADCAST & TEXT HANDLER ====================
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""

    # Payment Proof Processing
    if user_states.get(user_id) == "WAITING_PAYMENT_PROOF":
        user_states[user_id] = None
        await update.message.reply_text("✅ Payment proof submitted to Admin! Please wait for approval.")
        
        # Notify Admin
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve 1 Month", callback_data=f"adm_approve_{user_id}")]
        ])
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 **New Payment Request!**\n\n👤 **User:** {update.effective_user.full_name} (`{user_id}`)\n💬 **TRX/Proof:** `{text}`",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return

    # Admin Broadcast Waiting
    if user_states.get(user_id) == "WAITING_BROADCAST_MSG" and user_id == ADMIN_ID:
        user_states[user_id] = None
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        uids = c.fetchall()
        conn.close()

        sent = 0
        for uid in uids:
            try:
                await context.bot.send_message(chat_id=uid[0], text=f"📢 **Announcement:**\n\n{text}", parse_mode="Markdown")
                sent += 1
                await asyncio.sleep(0.05)
            except:
                pass
        await update.message.reply_text(f"✅ Broadcast Sent to `{sent}` users!")
        return

    # ❌ OTP BROADCAST COMMAND PARSER (e.g. 🇧🇩 #Bd WS 8801350❌❌1462 100cd 1s)
    parts = text.split()
    if len(parts) >= 4 and parts[-1].lower().endswith(("s", "m")) and parts[-2].lower().endswith("cd"):
        if user_id != ADMIN_ID and not is_subscribed(user_id):
            await update.message.reply_text("❌ Subscription required to generate OTP.")
            return
            
        time_part = parts.pop().lower()
        delay_seconds = float(time_part[:-1]) if time_part.endswith("s") else float(time_part[:-1]) * 60
        total_count = int(parts.pop().lower().replace("cd", ""))
        full_pattern = " ".join(parts)

        await update.message.reply_text(f"🚀 **OTP Task Started!**\nTotal: `{total_count}` | Delay: `{delay_seconds}s`", parse_mode="Markdown")
        asyncio.create_task(run_otp_loop(update.effective_chat.id, full_pattern, total_count, delay_seconds, context))

async def run_otp_loop(chat_id, full_pattern, total_count, delay_seconds, context):
    active_tasks[chat_id] = True
    
    formatted_pattern = full_pattern
    if " WS " in f" {formatted_pattern} " or " ws " in f" {formatted_pattern} ":
        formatted_pattern = re.sub(r'\b(WS|ws)\b', '🟢', formatted_pattern)
    elif " TG " in f" {formatted_pattern} " or " tg " in f" {formatted_pattern} ":
        formatted_pattern = re.sub(r'\b(TG|tg)\b', '✈️', formatted_pattern)

    for _ in range(total_count):
        if not active_tasks.get(chat_id, False):
            break

        final_line = formatted_pattern
        if len(final_line) > 4:
            random_last = "".join([str(random.randint(0, 9)) for _ in range(4)])
            final_line = final_line[:-4] + random_last

        otp_code = str(random.randint(100000, 999999))
        message_body = f"• {final_line}\n🔑 **OTP Code:** `{otp_code}`"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Copy Your Key", callback_data=f"copy_{otp_code}")],
            [
                InlineKeyboardButton("🤖 Get Number", url=SUPPORT_LINK),
                InlineKeyboardButton("📢 Support GP", url=SUPPORT_LINK)
            ]
        ])

        try:
            await context.bot.send_message(chat_id=chat_id, text=message_body, parse_mode="Markdown", reply_markup=keyboard)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except Exception:
            pass

        await asyncio.sleep(delay_seconds)
    active_tasks[chat_id] = False

# ==================== MAIN STARTUP ====================
if __name__ == "__main__":
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_all_messages))
    
    app.run_polling()
