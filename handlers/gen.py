import random
import os
import time
from telegram import Update
from telegram.ext import ContextTypes
from state import running_task, set_cooldown, reset_state, cancel_flag

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running_task, cancel_flag   # <-- IMPORTANT

    # Cooldown check
    from state import is_cooldown
    if is_cooldown():
        await update.message.reply_text("⏳ Bot is cooling down. Please wait 15 seconds.")
        return

    if running_task is not None:
        await update.message.reply_text("❌ Another task is running. Use /stop first.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /gen <bin> <count>\nExample: /gen 403163 10")
        return

    bin_prefix = context.args[0].strip()
    try:
        count = int(context.args[1])
    except:
        await update.message.reply_text("❌ Count must be a number.")
        return

    if count > 100:
        await update.message.reply_text("❌ Max 100 cards per generation.")
        return
    if not bin_prefix.isdigit() or len(bin_prefix) < 6:
        await update.message.reply_text("❌ BIN must be at least 6 digits.")
        return

    running_task = "gen"
    cancel_flag = False
    await update.message.reply_text(f"🌀 Generating {count} cards with BIN {bin_prefix}...")

    cards = []
    for _ in range(count):
        remaining = 16 - len(bin_prefix)
        suffix = ''.join([str(random.randint(0,9)) for _ in range(remaining)])
        card_num = bin_prefix + suffix
        month = str(random.randint(1,12)).zfill(2)
        year = str(random.randint(2026, 2035))
        cvv = str(random.randint(100,999)).zfill(3)
        cards.append(f"{card_num}|{month}|{year}|{cvv}")

    out_path = f"gen_{update.message.from_user.id}_{int(time.time())}.txt"
    with open(out_path, 'w') as f:
        f.write('\n'.join(cards))

    await update.message.reply_document(
        document=open(out_path, 'rb'),
        caption=f"✅ Generated {len(cards)} cards with BIN {bin_prefix}."
    )
    os.remove(out_path)

    running_task = None
    set_cooldown(10)
    await update.message.reply_text("⏳ Cooldown 10s before next command.")
