from telegram import Update
from telegram.ext import ContextTypes

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"👤 *User Info*\n• Name: {user.first_name}\n• ID: {user.id}\n• Plan: Pro\n• Mass Limit: 5000\n• Private Access: On\n• Plan Expires: 2126-05-06"
    await update.message.reply_text(text, parse_mode='Markdown')