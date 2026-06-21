import asyncio
import os
import time
from telegram import Update
from telegram.ext import ContextTypes
from utils.proxy import load_proxies
from tools.proxy_tester import test_proxies

async def pxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc and update.message.reply_to_message:
        doc = update.message.reply_to_message.document
    if not doc:
        await update.message.reply_text("❌ Reply to a `.txt` file with `/pxy` or attach it.")
        return
    if not doc.file_name or not doc.file_name.endswith('.txt'):
        await update.message.reply_text("❌ Only `.txt` files supported.")
        return
    await update.message.reply_text("🔄 Testing proxies...")
    file = await doc.get_file()
    tmp_path = f"temp_{update.message.from_user.id}_{int(time.time())}.txt"
    await file.download_to_drive(tmp_path)
    with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    os.remove(tmp_path)
    if not lines:
        await update.message.reply_text("❌ File empty.")
        return
    loop = asyncio.get_event_loop()
    working = await loop.run_in_executor(None, test_proxies, lines)
    if not working:
        await update.message.reply_text("❌ No working proxies found.")
        return
    with open("proxies.txt", 'w') as f:
        f.write('\n'.join(working))
    count = load_proxies()
    out_path = f"working_{update.message.from_user.id}_{int(time.time())}.txt"
    with open(out_path, 'w') as f:
        f.write('\n'.join(working))
    await update.message.reply_document(
        document=open(out_path, 'rb'),
        caption=f"✅ Found **{len(working)}** proxies.\nLoaded: {count}",
        parse_mode='Markdown'
    )
    os.remove(out_path)