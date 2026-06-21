from telegram import Update
from telegram.ext import ContextTypes
from state import running_task, cancel_flag, set_cooldown, reset_state

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cancel_flag
    if running_task is None:
        await update.message.reply_text("❌ No task running.")
        return
    cancel_flag = True
    await update.message.reply_text("⏹️ Stopping current task...")
    # Wait for task to check flag (we'll set cooldown after task finishes)
    # We'll handle cooldown in the task loop itself.