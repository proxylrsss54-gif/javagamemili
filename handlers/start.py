from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "🐉 **Welcome Lenin** »\n"
        "This bot promises you fast and safe checkups with different gateways! 🚀\n\n"
        "🤖 Bot Dev 🐉 Rift 🐉\n"
        "📦 Version 🐉 2.0 (Constantly Upgrading...)"
    )
    keyboard = [
        [InlineKeyboardButton("🚪 GATES", callback_data='main_gates')],
        [InlineKeyboardButton("👤 ACCOUNT", callback_data='main_account')],
        [InlineKeyboardButton("🛠 TOOLS", callback_data='main_tools')],
        [InlineKeyboardButton("❌ CLOSE", callback_data='main_close')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        with open("dragon.jpg", "rb") as photo:
            await update.message.reply_photo(photo, caption=caption, parse_mode='Markdown', reply_markup=reply_markup)
    except:
        await update.message.reply_text(caption, parse_mode='Markdown', reply_markup=reply_markup)