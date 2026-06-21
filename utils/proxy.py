import random

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