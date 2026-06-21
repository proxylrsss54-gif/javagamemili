from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from utils.proxy import load_proxies

from handlers.start import start
from handlers.account import account
from handlers.pxy import pxy
from handlers.check import check
from handlers.kill import kill
from handlers.gateways import shopify, stripe, razorpay, authorize, donation, adyen
from handlers.callback import callback

# 🆕 New handlers
from handlers.gen import gen
from handlers.fake import fake
from handlers.stop import stop

import os

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable not set!")

def main():
    load_proxies()
    app = Application.builder().token(TOKEN).build()

    # Basic
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("account", account))

    # Tools
    app.add_handler(CommandHandler("pxy", pxy))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("kill", kill))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("fake", fake))
    app.add_handler(CommandHandler("stop", stop))

    # Gateways
    app.add_handler(CommandHandler("shopify", shopify))
    app.add_handler(CommandHandler("stripe", stripe))
    app.add_handler(CommandHandler("razorpay", razorpay))
    app.add_handler(CommandHandler("authorize", authorize))
    app.add_handler(CommandHandler("donation", donation))
    app.add_handler(CommandHandler("adyen", adyen))

    # Inline keyboard
    app.add_handler(CallbackQueryHandler(callback))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()