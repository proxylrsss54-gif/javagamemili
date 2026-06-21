from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'main_gates':
        keyboard = [
            [InlineKeyboardButton("🛒 Shopify", callback_data='gate_shopify')],
            [InlineKeyboardButton("⚡ Stripe", callback_data='gate_stripe')],
            [InlineKeyboardButton("🪙 Razorpay", callback_data='gate_razorpay')],
            [InlineKeyboardButton("🏦 Authorize", callback_data='gate_authorize')],
            [InlineKeyboardButton("❤️ Donation", callback_data='gate_donation')],
            [InlineKeyboardButton("🔷 Adyen", callback_data='gate_adyen')],
            [InlineKeyboardButton("💀 KILL", callback_data='gate_kill')],
            [InlineKeyboardButton("🔍 CHECK", callback_data='gate_check')],
            [InlineKeyboardButton("⬅️ BACK", callback_data='main_back')],
        ]
        await query.edit_message_caption(
            caption="🔽 **Select a gateway**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif data == 'main_account':
        user = update.effective_user
        text = (
            f"👤 *User Info*\n"
            f"• Name: {user.first_name}\n"
            f"• ID: {user.id}\n"
            f"• Plan: Pro\n"
            f"• Mass Limit: 5000\n"
            f"• Private Access: On\n"
            f"• Plan Expires: 2126-05-06"
        )
        await query.edit_message_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data='main_back')]]),
            parse_mode='Markdown'
        )

    elif data == 'main_tools':
        await query.edit_message_caption(
            caption=(
                "🛠 **Tools Menu**\n\n"
                "🔹 **/pxy** – Test proxies\n"
                "🔹 **/check** – Check card(s) (inline or file)\n"
                "🔹 **/kill** – Kill card(s) (inline or file)\n"
                "🔹 **/gen `<bin>` `<count>`** – Generate random cards\n"
                "🔹 **/fake `<country>`** – Generate fake address (us/uk/de/in/bd/fr/it/es/au/ca)\n"
                "🔹 **/stop** – Stop running task (15s cooldown)"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data='main_back')]]),
            parse_mode='Markdown'
        )

    elif data == 'main_close':
        await query.edit_message_caption(caption="👋 Closed. Use /start to reopen.")

    elif data == 'main_back':
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
        await query.edit_message_caption(
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif data.startswith('gate_'):
        gateway = data.replace('gate_', '')
        await query.edit_message_caption(
            caption=(
                f"Send: `/{gateway} card|month|year|cvv`\n"
                f"Or reply a `.txt` file to `/check` or `/kill` for bulk processing."
            ),
            parse_mode='Markdown'
        )