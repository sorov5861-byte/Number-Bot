import os
import re
import random
import sqlite3
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ============================================================
#                    SECRET NUMBER BOT
#                         main.py
# ============================================================

# =========================
# BOT CONFIG
# =========================

BOT_TOKEN = "8875251875:AAG_UmQZsl8bfHMmR8DGM-kZ1dN0ITgzB84"

# এখানে আপনার Telegram ID বসাবেন
# একাধিক Admin হলে:
# ADMIN_IDS = [123456789, 987654321]
ADMIN_IDS = [5747820322]

MIN_WITHDRAW = 30

DB_NAME = "secret_number.db"


# ============================================================
#                    CUSTOM EMOJI IDs
# ============================================================

EMOJI = {

    # My Stats
    "username": "6152280926257684465",
    "telegram_id": "6086867401803532902",
    "subscription": "6104644116832853064",
    "subscription_price": "6084695716024821348",
    "duration": "6107109342161411278",
    "total_earning": "6105092867900840631",
    "balance": "6190336264940559752",

    # Subscription
    "active": "6087027281971127830",
    "inactive": "6206448624298104566",

    # Services
    "facebook": "6091599390621834528",
    "instagram": "5319160079465857105",
    "whatsapp": "6298323188849838091",
    "telegram": "6242460902872850889",
    "paypal": "6258109564676220200",
}


# ============================================================
#                         SERVICES
# ============================================================

SERVICES = {

    "facebook": {
        "name": "Facebook",
        "emoji": EMOJI["facebook"],
        "button": "📘 Facebook",
    },

    "instagram": {
        "name": "Instagram",
        "emoji": EMOJI["instagram"],
        "button": "📸 Instagram",
    },

    "whatsapp": {
        "name": "WhatsApp",
        "emoji": EMOJI["whatsapp"],
        "button": "🟢 WhatsApp",
    },

    "telegram": {
        "name": "Telegram",
        "emoji": EMOJI["telegram"],
        "button": "✈️ Telegram",
    },

    "paypal": {
        "name": "Paypal",
        "emoji": EMOJI["paypal"],
        "button": "💳 Paypal",
    },

    "tiktok": {
        "name": "TikTok",
        "emoji": None,
        "button": "🎵 TikTok",
    },

    "imo": {
        "name": "IMO",
        "emoji": None,
        "button": "💬 IMO",
    },
}


# Aliases
ALIASES = {
    "fb": "facebook",
    "facebook": "facebook",

    "int": "instagram",
    "ig": "instagram",
    "instagram": "instagram",
    "intagram": "instagram",

    "ws": "whatsapp",
    "wa": "whatsapp",
    "whatsapp": "whatsapp",

    "tg": "telegram",
    "telegram": "telegram",

    "py": "paypal",
    "paypal": "paypal",

    "tt": "tiktok",
    "tiktok": "tiktok",

    "imo": "imo",
}


# ============================================================
#                         DATABASE
# ============================================================

db = sqlite3.connect(DB_NAME, check_same_thread=False)
db.row_factory = sqlite3.Row


def database():

    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',

            banned INTEGER DEFAULT 0,

            subscription INTEGER DEFAULT 0,
            subscription_price TEXT DEFAULT '0$',
            duration TEXT DEFAULT '30DAY',

            total_earning TEXT DEFAULT '0$',
            balance REAL DEFAULT 0,

            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            service TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            country TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT
        )
    """)

    for service in SERVICES:

        cursor.execute(
            """
            INSERT OR IGNORE INTO services
            (service, enabled)
            VALUES (?, 1)
            """,
            (service,)
        )

    db.commit()


database()


# ============================================================
#                         HELPERS
# ============================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


def ensure_user(user):

    db.execute(
        """
        INSERT INTO users
        (user_id, username, first_name, created_at)

        VALUES (?, ?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
        username=excluded.username,
        first_name=excluded.first_name
        """,

        (
            user.id,
            user.username or "",
            user.first_name or "",
            datetime.now().isoformat(),
        )
    )

    db.commit()


def get_user(user_id):

    return db.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()


def custom_emoji(emoji_id, fallback):

    if not emoji_id:
        return fallback

    return f'<tg-emoji emoji-id="{emoji_id}">⭐</tg-emoji>'


def service_name(service):

    return SERVICES[service]["name"]


def service_emoji(service):

    data = SERVICES[service]

    if data["emoji"]:
        return custom_emoji(
            data["emoji"],
            data["button"].split()[0]
        )

    return data["button"].split()[0]


def active_services():

    rows = db.execute(
        """
        SELECT service
        FROM services
        WHERE enabled=1
        ORDER BY rowid
        """
    ).fetchall()

    return [row["service"] for row in rows]


def get_countries(service):

    return db.execute(
        """
        SELECT *
        FROM countries
        WHERE service=?
        ORDER BY id
        """,
        (service,)
    ).fetchall()


# ============================================================
#                         MAIN MENU
# ============================================================

def main_menu(user_id):

    buttons = [

        [
            InlineKeyboardButton(
                "📱 Get Number",
                callback_data="get_number"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 My Stats",
                callback_data="stats"
            )
        ],

        [
            InlineKeyboardButton(
                "💸 Withdrawal",
                callback_data="withdraw"
            )
        ],

        [
            InlineKeyboardButton(
                "🆘 Support",
                callback_data="support"
            )
        ],
    ]

    # Admin only
    if is_admin(user_id):

        buttons.append(
            [
                InlineKeyboardButton(
                    "⚙️ Admin Panel",
                    callback_data="admin"
                )
            ]
        )

    return InlineKeyboardMarkup(buttons)


# ============================================================
#                         /START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    ensure_user(user)

    row = get_user(user.id)

    if row["banned"]:

        await update.message.reply_text(
            "🚫 <b>You are banned from this bot.</b>",
            parse_mode=ParseMode.HTML
        )

        return

    await update.message.reply_text(

        "╔══════════════════════╗\n"
        "       <b>SECRET NUMBER BOT</b>\n"
        "╚══════════════════════╝\n\n"

        "🌟 Welcome!\n"
        "Select an option below:",

        parse_mode=ParseMode.HTML,

        reply_markup=main_menu(user.id)
    )


# ============================================================
#                       GET NUMBER
# ============================================================

async def get_number_page(query):

    buttons = []

    for service in active_services():

        buttons.append(
            [
                InlineKeyboardButton(
                    SERVICES[service]["button"],
                    callback_data=f"service:{service}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ]
    )

    await query.edit_message_text(

        "📍 <b>Select a service:</b>\n\n"
        "Choose the service you want.",

        parse_mode=ParseMode.HTML,

        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ============================================================
#                     SERVICE COUNTRIES
# ============================================================

async def service_page(query, service):

    buttons = []

    countries = get_countries(service)

    for country in countries:

        buttons.append(
            [
                InlineKeyboardButton(
                    country["country"],
                    callback_data=f"country:{country['id']}"
                )
            ]
        )

    if not buttons:

        buttons.append(
            [
                InlineKeyboardButton(
                    "⚠️ No Country Available",
                    callback_data="nothing"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="get_number"
            )
        ]
    )

    await query.edit_message_text(

        f"📍 <b>Select a country for "
        f"{service_emoji(service)} "
        f"{service_name(service)}:</b>",

        parse_mode=ParseMode.HTML,

        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ============================================================
#                         MY STATS
# ============================================================

async def stats_page(query, user_id):

    user = get_user(user_id)

    if user["subscription"]:

        sub = (
            custom_emoji(
                EMOJI["active"],
                "🟢"
            )
            + " Active"
        )

    else:

        sub = (
            custom_emoji(
                EMOJI["inactive"],
                "🔴"
            )
            + " Detective"
        )

    username = user["username"]

    if username:

        username = "@" + username

    else:

        username = "N/A"

    text = (

        "╔══════════════════════╗\n"
        "          <b>MY STATS</b>\n"
        "╚══════════════════════╝\n\n"

        f"{custom_emoji(EMOJI['username'], '👤')} "
        f"<b>Username:</b> {username}\n\n"

        f"{custom_emoji(EMOJI['telegram_id'], '🆔')} "
        f"<b>Telegram ID:</b> <code>{user_id}</code>\n\n"

        f"{custom_emoji(EMOJI['subscription'], '📋')} "
        f"<b>My Subscription:</b> {sub}\n\n"

        f"{custom_emoji(EMOJI['subscription_price'], '💵')} "
        f"<b>Subscription Price:</b> "
        f"{user['subscription_price']}\n\n"

        f"{custom_emoji(EMOJI['duration'], '⏳')} "
        f"<b>Duration:</b> "
        f"{user['duration']}\n\n"

        f"{custom_emoji(EMOJI['total_earning'], '💰')} "
        f"<b>Total Earning:</b> "
        f"{user['total_earning']}\n\n"

        f"{custom_emoji(EMOJI['balance'], '💳')} "
        f"<b>My Balance:</b> "
        f"{user['balance']:.2f} Tk"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data="stats"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ]
    ]

    await query.edit_message_text(

        text,

        parse_mode=ParseMode.HTML,

        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
#                         WITHDRAW
# ============================================================

async def withdraw_page(query):

    keyboard = [

        [
            InlineKeyboardButton(
                "💳 Nagad",
                callback_data="withdraw:Nagad"
            )
        ],

        [
            InlineKeyboardButton(
                "💳 Rocket",
                callback_data="withdraw:Rocket"
            )
        ],

        [
            InlineKeyboardButton(
                "💳 Binnace",
                callback_data="withdraw:Binance"
            )
        ],

        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="home"
            )
        ]
    ]

    text = (

        "╔══════════════════════╗\n"
        "        <b>WITHDRAWAL</b>\n"
        "╚══════════════════════╝\n\n"

        "🔥 <b>Total Otp:</b> 0\n\n"

        "👥 <b>Total Reffer:</b> 0\n\n"

        "💰 <b>BALANCE:</b> 0 Tk\n\n"

        f"🔒 <b>MINIMUM:</b> {MIN_WITHDRAW} Tk\n\n"

        "<b>SELECT METHOD</b>"
    )

    await query.edit_message_text(

        text,

        parse_mode=ParseMode.HTML,

        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
#                         SUPPORT
# ============================================================

async def support_page(query):

    rows = db.execute(
        "SELECT * FROM supports ORDER BY id"
    ).fetchall()

    buttons = []

    for row in rows:

        value = row["value"]

        if value.startswith("https://t.me/"):

            buttons.append(
                [
                    InlineKeyboardButton(
                        f"🆘 {value}",
                        url=value
                    )
                ]
            )

        elif value.startswith("@"):

            buttons.append(
                [
                    InlineKeyboardButton(
                        f"🆘 {value}",
                        url=f"https://t.me/{value[1:]}"
                    )
                ]
            )

        else:

            buttons.append(
                [
                    InlineKeyboardButton(
                        f"🆘 {value}",
                        callback_data="support_info"
                    )
                ]
            )

    if not buttons:

        buttons.append(
            [
                InlineKeyboardButton(
                    "⚠️ Support not configured",
                    callback_data="nothing"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ]
    )

    await query.edit_message_text(

        "🆘 <b>SUPPORT</b>\n\n"
        "Select a support contact:",

        parse_mode=ParseMode.HTML,

        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ============================================================
#                         ADMIN PANEL
# ============================================================

async def admin_page(query):

    if not is_admin(query.from_user.id):

        await query.answer(
            "❌ Admin Only",
            show_alert=True
        )

        return

    keyboard = [

        [
            InlineKeyboardButton(
                "📢 Broadcast",
                callback_data="admin_broadcast"
            ),

            InlineKeyboardButton(
                "📊 Stats",
                callback_data="admin_stats"
            )
        ],

        [
            InlineKeyboardButton(
                "🆘 Support",
                callback_data="admin_support"
            ),

            InlineKeyboardButton(
                "🚫 Ban / Unban",
                callback_data="admin_ban"
            )
        ],

        [
            InlineKeyboardButton(
                "📱 Get Number",
                callback_data="admin_services"
            )
        ],

        [
            InlineKeyboardButton(
                "🌍 Country Manager",
                callback_data="admin_countries"
            )
        ],

        [
            InlineKeyboardButton(
                "👤 User Stats",
                callback_data="admin_userstats"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ]
    ]

    await query.edit_message_text(

        "╔══════════════════════╗\n"
        "         <b>ADMIN PANEL</b>\n"
        "╚══════════════════════╝\n\n"

        "⚙️ Select management option:",

        parse_mode=ParseMode.HTML,

        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
#                     /getnumber_set
# ============================================================

async def getnumber_set(update, context):

    if not is_admin(update.effective_user.id):
        return

    text = update.message.text

    parts = text.split(maxsplit=1)

    if len(parts) < 2:

        await update.message.reply_text(
            "Example:\n\n"
            "/getnumber_set Instagram Facebook WhatsApp"
        )

        return

    names = re.split(
        r"[\s,]+",
        parts[1]
    )

    added = []

    for name in names:

        key = ALIASES.get(
            name.lower().strip()
        )

        if not key:
            continue

        db.execute(
            """
            UPDATE services
            SET enabled=1
            WHERE service=?
            """,
            (key,)
        )

        added.append(
            SERVICES[key]["name"]
        )

    db.commit()

    if added:

        await update.message.reply_text(
            "✅ <b>Services Enabled</b>\n\n"
            + "\n".join(
                f"🟢 {x}" for x in added
            ),
            parse_mode=ParseMode.HTML
        )

    else:

        await update.message.reply_text(
            "❌ No valid service found."
