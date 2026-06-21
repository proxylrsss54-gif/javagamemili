import os
import asyncio
import time
from telegram import Update
from telegram.ext import ContextTypes
from utils.proxy import load_proxies
from gates.authorize import authorize_check
from kill.kill import check_cmd as check_inline
from .helpers import (
    extract_cards_from_text,
    ensure_proxy,
    update_progress_message,
    format_bin_info
)
from state import running_task, cancel_flag, set_cooldown, reset_state

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running_task, cancel_flag

    from state import is_cooldown
    if is_cooldown():
        await update.message.reply_text("⏳ Bot is cooling down. Please wait 15 seconds.")
        return

    if running_task is not None:
        await update.message.reply_text("❌ Another task is running. Use /stop first.")
        return

    ensure_proxy()
    doc = update.message.document
    if not doc and update.message.reply_to_message:
        doc = update.message.reply_to_message.document

    if doc:
        if not doc.file_name or not doc.file_name.endswith('.txt'):
            await update.message.reply_text("❌ Only `.txt` files are supported.")
            return

        status_msg = await update.message.reply_text("📄 Reading file...")
        file = await doc.get_file()
        tmp_path = f"temp_{update.message.from_user.id}_{int(time.time())}.txt"
        await file.download_to_drive(tmp_path)

        with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        os.remove(tmp_path)

        cards = extract_cards_from_text(content)
        if not cards:
            await status_msg.edit_text("❌ No valid cards found.")
            return

        total = len(cards)
        live = 0
        dead = 0
        results = []
        running_task = "check"
        cancel_flag = False

        for idx, (card, month, year, cvv) in enumerate(cards, 1):
            if cancel_flag:
                await status_msg.edit_text("⏹️ Stopped by user.")
                break

            status, msg, is_live = await authorize_check(card, month, year, cvv)

            if is_live is True:
                live += 1
                emoji = "✅"
            elif is_live is False:
                dead += 1
                emoji = "❌"
            else:
                emoji = "⚠️"

            bin_prefix = card[:6]
            bin_text = format_bin_info(bin_prefix)

            results.append(
                f"{emoji} **Card:** {card[:6]}******{card[-4:]} | {month}/{year} | CVV {cvv}\n"
                f"**Gateway:** Authorize\n"
                f"**Status:** {status}\n"
                f"**Response:** {msg}\n"
                f"{bin_text}\n"
                f"---"
            )

            if idx % 2 == 0 or idx == total:
                await update_progress_message(status_msg, idx, total, live, dead, "Checking")

        running_task = None
        set_cooldown(15)
        await status_msg.edit_text(
            f"✅ **Check Complete**\n\n" + "\n".join(results) + "\n\n⏳ Cooldown 15s"
        )
        return

    # Inline mode
    await check_inline(update, context)
