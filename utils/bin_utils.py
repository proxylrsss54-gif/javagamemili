import requests
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_bin_info(bin_prefix):
    try:
        r = requests.get(f"https://lookup.binlist.net/{bin_prefix}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                'brand': data.get('brand', 'UNKNOWN'),
                'type': data.get('type', 'UNKNOWN'),
                'category': data.get('category', 'UNKNOWN'),
                'bank': data.get('bank', {}).get('name', 'UNKNOWN'),
                'country': data.get('country', {}).get('name', 'UNKNOWN'),
                'country_code': data.get('country', {}).get('alpha2', 'XX'),
                'flag': data.get('country', {}).get('emoji', '🏳️')
            }
        else:
            return None
    except:
        return None