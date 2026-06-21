from faker import Faker
from telegram import Update
from telegram.ext import ContextTypes
import random

# Map country codes to Faker locales
LOCALE_MAP = {
    'us': 'en_US',
    'uk': 'en_GB',
    'de': 'de_DE',
    'in': 'en_IN',
    'bd': 'bn_BD',
    'fr': 'fr_FR',
    'it': 'it_IT',
    'es': 'es_ES',
    'au': 'en_AU',
    'ca': 'en_CA',
    # add more as needed
}

async def fake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("❌ Usage: /fake <country_code>\nExample: /fake us\nSupported: us, uk, de, in, bd, fr, it, es, au, ca")
        return
    code = context.args[0].lower()
    if code not in LOCALE_MAP:
        await update.message.reply_text("❌ Unsupported country code. Use: us, uk, de, in, bd, fr, it, es, au, ca")
        return
    locale = LOCALE_MAP[code]
    fake = Faker(locale)
    # Generate identity
    first_name = fake.first_name()
    last_name = fake.last_name()
    gender = random.choice(['Male', 'Female'])
    dob = fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d')
    street = fake.street_address()
    city = fake.city()
    state = fake.state()
    postcode = fake.postcode()
    country = fake.country()
    email = fake.email()
    phone = fake.phone_number()
    cell = fake.phone_number()
    # Build response
    text = (
        f"📍 **Real Address — {country.upper()}**\n\n"
        f"• **Name:** {first_name} {last_name}\n"
        f"• **Gender:** {gender}\n"
        f"• **DOB:** {dob}\n\n"
        f"• **Street:** {street}\n"
        f"• **City:** {city}\n"
        f"• **State:** {state}\n"
        f"• **Postcode:** {postcode}\n"
        f"• **Country:** {country}\n\n"
        f"• **Email:** {email}\n"
        f"• **Phone:** {phone}\n"
        f"• **Cell:** {cell}"
    )
    await update.message.reply_text(text, parse_mode='Markdown')