import time
from telegram import Update
from telegram.ext import ContextTypes
from utils.proxy import load_proxies
from gates.shopify import shopify_check
from gates.stripe import stripe_check
from gates.razorpay import razorpay_check
from gates.adyen import adyen_check
from gates.authorize import authorize_check
from .helpers import ensure_proxy, format_bin_info

async def gateway_command(update: Update, context: ContextTypes.DEFAULT_TYPE, gateway_name: str):
    ensure_proxy()
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
    start_time = time.time()

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

    elapsed = time.time() - start_time
    emoji = "✅" if live is True else "❌" if live is False else "⚠️"
    bin_prefix = card[:6]
    bin_text = format_bin_info(bin_prefix)
    user_name = update.effective_user.username or update.effective_user.first_name

    reply = (
        f"{emoji} **Card:** {card[:6]}******{card[-4:]} | {month}/{year} | CVV {cvv}\n"
        f"**Gateway:** {gateway_name.upper()}\n"
        f"**Status:** {status}\n"
        f"**Response:** {msg}\n"
        f"{bin_text}\n"
        f"**Checked By:** @{user_name}\n"
        f"**Time:** {elapsed:.2f}s"
    )
    await update.message.reply_text(reply, parse_mode='Markdown')

# Command wrappers
async def shopify(update, context):
    await gateway_command(update, context, 'shopify')

async def stripe(update, context):
    await gateway_command(update, context, 'stripe')

async def razorpay(update, context):
    await gateway_command(update, context, 'razorpay')

async def authorize(update, context):
    await gateway_command(update, context, 'authorize')

async def donation(update, context):
    await gateway_command(update, context, 'donation')

async def adyen(update, context):
    await gateway_command(update, context, 'adyen')