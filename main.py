import os
import re
import random
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# WEB SERVER FOR UPTIMEROBOT
# =========================
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


# =========================
# CONFIG
# =========================
BOT_TOKEN = "8871976724:AAErqWjPFxSn-AyBBqQxO9nVHMA6h1mIuVY"  # আপনার বট টোকেন দিন
ADMIN_ID = 5747820322              # আপনার টেলিগ্রাম আইডি দিন
MAX_ENTRIES = 100

demo_entries = []


# =========================
# HELPERS
# =========================
def generate_number(prefix: str):
    clean_prefix = re.sub(r"\D", "", prefix)
    if len(clean_prefix) < 5:
        return None

    fixed = clean_prefix[:5]
    remaining_length = random.choice([5, 6, 7])
    random_part = "".join(random.choice("0123456789") for _ in range(remaining_length))

    return fixed + random_part

def generate_code():
    return str(random.randint(100000, 999999))

def add_demo_entry(country, service, number):
    code = generate_code()
    entry = {
        "country": country,
        "service": service,
        "number": number,
        "code": code,
        "time": datetime.now().strftime("%H:%M:%S"),
    }
    demo_entries.append(entry)
    if len(demo_entries) > MAX_ENTRIES:
        demo_entries.pop(0)
    return entry

def format_entry(entry):
    return (
        f"🌐 {entry['country']} {entry['service']}\n"
        f"📱 {entry['number']}\n"
        f"🔢 {entry['code']}\n"
        f"🕐 {entry['time']}"
    )


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 Demo Generator", callback_data="generator")],
        [InlineKeyboardButton("📊 Demo Traffic", callback_data="traffic")],
    ]
    await update.message.reply_text(
        "🔥 <b>Premium Demo Number Bot</b>\n\n"
        "এটি শুধুমাত্র testing/demo traffic-এর জন্য।\n\n"
        "নিচের button ব্যবহার করো অথবা লিখো:\n\n"
        "<code>🇵🇸 WhatsApp 249738383</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BUTTON HANDLER
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # কপি বাটন অ্যালার্ট হ্যান্ডলিং
    if data.startswith("copy_"):
        code = data.split("_")[1]
        await query.answer(text=f"🔑 Copied Code: {code}", show_alert=True)
        return

    await query.answer()

    if data == "generator":
        await query.message.reply_text(
            "🎯 <b>Demo Generator</b>\n\n"
            "এই format-এ পাঠাও:\n\n"
            "<code>🇵🇸 WhatsApp 249738383</code>\n\n"
            "প্রথম ৫টি digit একই রেখে demo number তৈরি হবে।",
            parse_mode="HTML"
        )

    elif data == "traffic":
        if not demo_entries:
            await query.message.reply_text("📭 এখনো কোনো Demo Traffic নেই।")
            return

        text = "🔥 <b>DEMO LIVE TRAFFIC</b>\n\n"
        for entry in demo_entries[-15:]:
            text += f"{format_entry(entry)}\n━━━━━━━━━━━━━━\n"

        await query.message.reply_text(text, parse_mode="HTML")


# =========================
# MESSAGE PARSER
# =========================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    match = re.search(
        r"(.+?)\s+(WhatsApp|Telegram|Instagram|Facebook|Discord|WS|TG)\s+(\d+)",
        text,
        re.IGNORECASE
    )

    if not match:
        return

    country = match.group(1).strip()
    service = match.group(2).strip()
    prefix = match.group(3).strip()

    number = generate_number(prefix)

    if not number:
        await update.message.reply_text(
            "❌ কমপক্ষে ৫টি digit দিতে হবে।\n\n"
            "Example:\n<code>🇵🇸 WhatsApp 249738383</code>",
            parse_mode="HTML"
        )
        return

    entry = add_demo_entry(country, service, number)

    # লোগো সিলেক্টর
    logo = "🟢"
    if "telegram" in service.lower() or "tg" in service.lower():
        logo = "✈️"

    keyboard = [
        [InlineKeyboardButton(f"{logo}  📋 {entry['code']}", callback_data=f"copy_{entry['code']}")]
    ]

    await update.message.reply_text(
        f"{country} {service} {number}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ADMIN COMMANDS
# =========================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin access required.")
        return

    await update.message.reply_text(
        "👑 <b>ADMIN PANEL</b>\n\n"
        "/traffic - Demo traffic দেখুন\n"
        "/clear - সব demo traffic delete\n"
        "/generate <prefix> - automatic demo entries\n",
        parse_mode="HTML"
    )

async def traffic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not demo_entries:
        await update.message.reply_text("📭 No demo traffic.")
        return

    text = "🔥 <b>DEMO TRAFFIC</b>\n\n"
    for entry in demo_entries:
        text += f"{format_entry(entry)}\n━━━━━━━━━━━━━━\n"

    await update.message.reply_text(text, parse_mode="HTML")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    demo_entries.clear()
    await update.message.reply_text("🗑️ Demo traffic cleared.")

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only.")
        return

    if not context.args:
        await update.message.reply_text("Usage:\n<code>/generate 249738383</code>", parse_mode="HTML")
        return

    prefix = context.args[0]
    if not prefix.isdigit() or len(prefix) < 5:
        await update.message.reply_text("❌ Minimum 5 digits required.")
        return

    chat_id = update.effective_chat.id
    delays = [5, 20, 50, 60, 120]

    await update.message.reply_text("🚀 Auto generation started in background...")

    for delay in delays:
        await asyncio.sleep(delay)
        number = generate_number(prefix)
        entry = add_demo_entry("🇵🇸", "WhatsApp", number)

        keyboard = [
            [InlineKeyboardButton(f"🟢  📋 {entry['code']}", callback_data=f"copy_{entry['code']}")]
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🇵🇸 WhatsApp {number}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================
# MAIN
# =========================
def main():
    keep_alive()  # Flask Web Server Start

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("traffic", traffic))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🔥 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
