import asyncio
import random
import re
import os
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.error import RetryAfter

# --- Keep Alive Server (UptimeRobot) ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "Number Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- Configuration & Constants ---
BOT_TOKEN = "8862245246:AAGIMWcpv7d7yotl9b40tAS32HiRAib3krM"
ADMIN_ID = 5747820322

# Premium Emoji IDs
EMOJI_STATS_USERNAME = "6152280926257684465"
EMOJI_STATS_TGID = "6086867401813532902"
EMOJI_STATS_SUB = "6104644116832853064"
EMOJI_STATS_PRICE = "6084695716024821348"
EMOJI_STATS_DURATION = "6107109342161411278"
EMOJI_STATS_EARNING = "6105092867900840631"
EMOJI_STATS_BALANCE = "6190336264940559752"

EMOJI_ACTIVE = "6087027281971127830"
EMOJI_DETECTIVE = "6206448624298104566"

EMOJI_FB = "6091599390621834528"
EMOJI_INT = "5319160079465857105"
EMOJI_WS = "6298323188849838091"
EMOJI_TG = "6242460902872850889"
EMOJI_PY = "6258109564676220200"

# --- In-Memory Database / Data Structures ---
users_db = {}     # user_id -> dict(banned, status, price, duration, earning, balance)
services_db = [   # Default services
    "Instagram", "Facebook", "WhatsApp", "Telegram", "Paypal", "Tiktok"
]
countries_db = {} # service_name -> list of strings (e.g., "🇵🇸 Sudan - 0.8Tk/OTP")
support_links = ["https://t.me/telegram"]

# Platform mappings for Emojis
PLATFORM_EMOJIS = {
    "facebook": (EMOJI_FB, "Facebook", "📘"),
    "fb": (EMOJI_FB, "Facebook", "📘"),
    "instagram": (EMOJI_INT, "Instagram", "📸"),
    "int": (EMOJI_INT, "Instagram", "📸"),
    "whatsapp": (EMOJI_WS, "WhatsApp", "🟢"),
    "ws": (EMOJI_WS, "WhatsApp", "🟢"),
    "telegram": (EMOJI_TG, "Telegram", "✈️"),
    "tg": (EMOJI_TG, "Telegram", "✈️"),
    "paypal": (EMOJI_PY, "Paypal", "🅿️"),
    "py": (EMOJI_PY, "Paypal", "🅿️"),
}

def get_user_data(user_id: int):
    if user_id not in users_db:
        users_db[user_id] = {
            "banned": False,
            "status": "🔴 Detective",
            "price": "0$",
            "duration": "0DAY",
            "earning": "0$",
            "balance": "0.0৳"
        }
    return users_db[user_id]

def build_main_keyboard(user_id: int):
    keyboard = [
        ["📱 Get Number", "📊 My Stats"],
        ["💳 Withdraw", "🎧 Support"]
    ]
    if user_id == ADMIN_ID:
        keyboard.append(["⚙️ Admin Panel"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- Command Handlers ---

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_data(user_id)
    
    if users_db[user_id]["banned"]:
        await update.message.reply_text("❌ You are banned from using this bot.")
        return

    welcome_text = "👋 <b>Welcome to SECRET NUMBER BOT!</b>\n\nChoose an option from the menu below:"
    await update.message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_id)
    )

async def copy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    code = query.data.split("_")[-1]
    await query.answer(text=f"🔑 OTP Code: {code}", show_alert=True)

# --- Text Handler for Menu & Admin Commands ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    if user_data["banned"]:
        await update.message.reply_text("❌ You are banned from using this bot.")
        return

    text = update.message.text.strip()

    # --- 1. GET NUMBER ---
    if text == "📱 Get Number":
        keyboard = []
        for s in services_db:
            s_lower = s.lower()
            emoji_code = "📱"
            if s_lower in PLATFORM_EMOJIS:
                e_id, _, alt = PLATFORM_EMOJIS[s_lower]
                emoji_code = f'<tg-emoji emoji-id="{e_id}">{alt}</tg-emoji>'
            keyboard.append([InlineKeyboardButton(f"{s}", callback_data=f"srv_{s}")])
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])

        await update.message.reply_text(
            "<b>🧿 Select a service:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --- 2. MY STATS ---
    elif text == "📊 My Stats":
        username = update.effective_user.username
        username_str = f"@{username}" if username else "N/A"

        status_val = user_data["status"]
        if "Active" in status_val:
            status_html = f'<tg-emoji emoji-id="{EMOJI_ACTIVE}">🟢</tg-emoji> Active'
        else:
            status_html = f'<tg-emoji emoji-id="{EMOJI_DETECTIVE}">🔴</tg-emoji> Detective'

        stats_msg = (
            f'<tg-emoji emoji-id="{EMOJI_STATS_USERNAME}">👤</tg-emoji> <b>Username:</b> {username_str}\n'
            f'<tg-emoji emoji-id="{EMOJI_STATS_TGID}">🆔</tg-emoji> <b>Telegram ID:</b> <code>{user_id}</code>\n'
            f'<tg-emoji emoji-id="{EMOJI_STATS_SUB}">📜</tg-emoji> <b>My Subscription:</b> {status_html}\n'
            f'<tg-emoji emoji-id="{EMOJI_STATS_PRICE}">💵</tg-emoji> <b>Subscription Price:</b> {user_data["price"]}\n'
            f'<tg-emoji emoji-id="{EMOJI_STATS_DURATION}">⏳</tg-emoji> <b>Duration:</b> {user_data["duration"]}\n'
            f'<tg-emoji emoji-id="{EMOJI_STATS_EARNING}">💰</tg-emoji> <b>Total Earning:</b> {user_data["earning"]}\n'
            f'<tg-emoji emoji-id="{EMOJI_STATS_BALANCE}">💳</tg-emoji> <b>My Balance:</b> {user_data["balance"]}'
        )

        await update.message.reply_text(stats_msg, parse_mode="HTML")
        return

    # --- 3. WITHDRAWAL ---
    elif text == "💳 Withdraw":
        withdraw_text = (
            "▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️\n"
            "《 🥷 <b>WITHDRAWAL</b> 》\n"
            "▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️\n"
            "👏 <b>Total Otp:</b> 0\n"
            "▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️\n"
            "👥 <b>Total Reffer:</b> 0\n"
            "▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️\n"
            f"📅 <b>BALANCE:</b> {user_data['balance']}\n"
            "▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️\n"
            "🛡️ <b>MINIMUM:</b> 30.0 ৳\n"
            "▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️\n"
            "<b>SELECT METHOD:</b>"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👛 Nagad", callback_data="w_method")],
            [InlineKeyboardButton("👛 Rocket", callback_data="w_method")],
            [InlineKeyboardButton("👛 Binance", callback_data="w_method")],
            [InlineKeyboardButton("❌ Cancel", callback_data="close_menu")]
        ])
        await update.message.reply_text(withdraw_text, parse_mode="HTML", reply_markup=keyboard)
        return

    # --- 4. SUPPORT ---
    elif text == "🎧 Support":
        if not support_links:
            await update.message.reply_text("No support accounts configured currently.")
            return
        keyboard = []
        for idx, link in enumerate(support_links, 1):
            keyboard.append([InlineKeyboardButton(f"🎧 Support Agent {idx}", url=link)])
        await update.message.reply_text(
            "<b> Contact Support Team:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --- 5. ADMIN PANEL ---
    elif text == "⚙️ Admin Panel" and user_id == ADMIN_ID:
        admin_text = "🛠️ <b>ADMIN CONTROL PANEL</b>\nChoose an action to perform:"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast"), InlineKeyboardButton("📊 Bot Stats", callback_data="adm_stats")],
            [InlineKeyboardButton("🎧 Support Settings", callback_data="adm_support")],
            [InlineKeyboardButton("🚫 Ban User", callback_data="adm_ban"), InlineKeyboardButton("✅ Unban User", callback_data="adm_unban")]
        ])
        await update.message.reply_text(admin_text, parse_mode="HTML", reply_markup=keyboard)
        return

    # --- ADMIN COMMANDS ---
    if user_id == ADMIN_ID:
        # Service Management Commands
        if text.startswith("/getnumber_set"):
            lines = text.split("\n")[1:]
            for line in lines:
                s_name = line.strip()
                if s_name and s_name not in services_db:
                    services_db.append(s_name)
            await update.message.reply_text("✅ Services updated successfully!")
            return

        elif text.startswith("/getnumber_remove_"):
            s_rem = text.replace("/getnumber_remove_", "").strip()
            if s_rem in services_db:
                services_db.remove(s_rem)
                await update.message.reply_text(f"✅ Service '{s_rem}' removed.")
            else:
                await update.message.reply_text("❌ Service not found.")
            return

        # Country Management Commands
        elif text.startswith("/getnumber_") and "_country" in text:
            # Example: /getnumber_instagram_country\n🇵🇸 Sudan - 0.8Tk/OTP
            header, *c_lines = text.split("\n")
            srv_key = header.replace("/getnumber_", "").replace("_country", "").strip().lower()

            if srv_key not in countries_db:
                countries_db[srv_key] = []
            for line in c_lines:
                c_item = line.strip()
                if c_item and c_item not in countries_db[srv_key]:
                    countries_db[srv_key].append(c_item)
            await update.message.reply_text(f"✅ Countries added for '{srv_key}'.")
            return

        elif text.startswith("/getnumber_country_") and text.endswith("_remov"):
            # Example: /getnumber_country_🇵🇸 Sudan - 0.8TK/OTP_remov
            raw = text.replace("/getnumber_country_", "").replace("_remov", "").strip()
            found = False
            for k in countries_db:
                if raw in countries_db[k]:
                    countries_db[k].remove(raw)
                    found = True
            if found:
                await update.message.reply_text("✅ Country removed successfully.")
            else:
                await update.message.reply_text("❌ Country format not found.")
            return

        # User Stats Admin Command
        elif text.startswith("/set_userstasts_"):
            lines = text.split("\n")
            target_uid = int(lines[0].replace("/set_userstasts_", "").strip())
            u_data = get_user_data(target_uid)

            for line in lines[1:]:
                if "Subscription :-" in line:
                    u_data["status"] = line.split(":-")[1].strip()
                elif "Subscription Price :-" in line:
                    u_data["price"] = line.split(":-")[1].strip()
                elif "Duration :-" in line:
                    u_data["duration"] = line.split(":-")[1].strip()
                elif "Total Earning :-" in line:
                    u_data["earning"] = line.split(":-")[1].strip()
                elif "My Balance :-" in line:
                    u_data["balance"] = line.split(":-")[1].strip()

            await update.message.reply_text(f"✅ Stats updated for User ID {target_uid}.")
            return

    # --- 6. OTP/NUMBER PARSER COMMAND (e.g. 🇧🇩 BD ws WhatsApp 88017738635862) ---
    parts = text.split()
    if len(parts) >= 3 and any(char.isdigit() for char in parts[-1]):
        plat_key = None
        for p in parts:
            p_low = p.lower()
            if p_low in PLATFORM_EMOJIS:
                plat_key = p_low
                break

        if plat_key:
            emoji_id, name, alt = PLATFORM_EMOJIS[plat_key]
            country_flag = parts[0]
            number = parts[-1]
            
            header_text = f"<b>{country_flag} <tg-emoji emoji-id=\"{emoji_id}\">{alt}</tg-emoji> {name.upper()} {number}</b>"
            otp_code = str(random.randint(100000, 999999))
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📋 {otp_code}", callback_data=f"copy_{otp_code}")]
            ])

            await update.message.reply_text(
                header_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            return

# --- Callback Query Handler (Inline Button Presses) ---

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    user_data = get_user_data(user_id)

    if data == "close_menu":
        await query.message.delete()
        return

    elif data == "w_method":
        await query.answer(text="Minimum Withdraw 30 Tk ❌", show_alert=True)
        return

    # Service Selection Process
    elif data.startswith("srv_"):
        srv_name = data.replace("srv_", "")
        srv_key = srv_name.lower()
        country_list = countries_db.get(srv_key, [])

        keyboard = []
        for c in country_list:
            keyboard.append([InlineKeyboardButton(c, callback_data=f"cntry_{c}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_services")])

        await query.message.edit_text(
            f"<b>📍 Select a country for {srv_name.upper()}:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    elif data == "back_to_services":
        keyboard = []
        for s in services_db:
            keyboard.append([InlineKeyboardButton(s, callback_data=f"srv_{s}")])
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])

        await query.message.edit_text(
            "<b>🧿 Select a service:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    elif data.startswith("cntry_"):
        if "Active" not in user_data["status"]:
            await query.answer(text="Your subscription not active ❌", show_alert=True)
        else:
            await query.answer(text="Country Selected! Contact admin for numbers.", show_alert=True)
        return

    # Admin Callback Features
    elif data == "adm_stats" and user_id == ADMIN_ID:
        total_u = len(users_db)
        await query.answer(text=f"📊 Total Users: {total_u}", show_alert=True)

    elif data == "adm_support" and user_id == ADMIN_ID:
        msg = "Send new support format:\n/set_support https://t.me/username"
        await query.message.reply_text(msg)

    elif data in ["adm_broadcast", "adm_ban", "adm_unban"] and user_id == ADMIN_ID:
        await query.answer(text="Use text commands for this feature.", show_alert=True)

# --- Main Application Setup ---

if __name__ == "__main__":
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(copy_callback, pattern="^copy_"))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_polling()
