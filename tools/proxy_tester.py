import socket
import socks
import requests
import concurrent.futures
import re
import time

TIMEOUT = 6
TEST_URL = "http://httpbin.org/ip"

def parse_proxy_line(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    # Remove protocol prefix if exists
    protocol = 'http'
    rest = line
    if '://' in line:
        protocol_part, rest = line.split('://', 1)
        if protocol_part in ['http', 'https', 'socks4', 'socks5']:
            protocol = protocol_part
    # Extract ip and port
    parts = rest.split(':')
    if len(parts) >= 2:
        ip = parts[0].strip()
        port = parts[1].strip()
        # handle if there's trailing stuff (like | etc)
        port = re.sub(r'[^0-9]', '', port)
        if ip and port:
            return {'protocol': protocol, 'ip': ip, 'port': int(port), 'original': line}
    return None

def test_single_proxy(proxy_info):
    protocol = proxy_info['protocol']
    ip = proxy_info['ip']
    port = proxy_info['port']
    original = proxy_info['original']
    
    if protocol in ['http', 'https']:
        proxy_dict = {
            'http': f'http://{ip}:{port}',
            'https': f'http://{ip}:{port}'
        }
        try:
            r = requests.get(TEST_URL, proxies=proxy_dict, timeout=TIMEOUT)
            if r.status_code == 200:
                return original
        except:
            pass
    elif protocol == 'socks4':
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS4, ip, port)
            s.settimeout(TIMEOUT)
            s.connect(('httpbin.org', 80))
            s.send(b"GET /ip HTTP/1.0\r\nHost: httpbin.org\r\n\r\n")
            data = s.recv(1024)
            s.close()
            if b'200' in data:
                return original
        except:
            pass
    elif protocol == 'socks5':
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, ip, port)
            s.settimeout(TIMEOUT)
            s.connect(('httpbin.org', 80))
            s.send(b"GET /ip HTTP/1.0\r\nHost: httpbin.org\r\n\r\n")
            data = s.recv(1024)
            s.close()
            if b'200' in data:
                return original
        except:
            pass
    return None

def test_proxies(lines, max_workers=30):
    proxies = []
    for line in lines:
        p = parse_proxy_line(line)
        if p:
            proxies.append(p)
    
    if not proxies:
        return []
    
    working = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {executor.submit(test_single_proxy, p): p for p in proxies}
        for future in concurrent.futures.as_completed(future_to_proxy):
            result = future.result()
            if result:
                working.append(result)
    return working