import re
from utils.proxy import load_proxies

def ensure_proxy():
    return load_proxies()

def parse_card_line(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    for sep in ['|', '/', ':']:
        if sep in line:
            parts = line.split(sep)
            if len(parts) >= 4:
                card = parts[0].strip()
                month = parts[1].strip().zfill(2)
                year = parts[2].strip()
                cvv = parts[3].strip()
                if len(year) == 2:
                    year = f"20{year}"
                return (card, month, year, cvv)
    parts = line.split()
    if len(parts) >= 4:
        card = parts[0].strip()
        month = parts[1].strip().zfill(2)
        year = parts[2].strip()
        cvv = parts[3].strip()
        if len(year) == 2:
            year = f"20{year}"
        return (card, month, year, cvv)
    return None

def extract_cards_from_text(text):
    cards = []
    for line in text.split('\n'):
        parsed = parse_card_line(line)
        if parsed:
            cards.append(parsed)
    return cards

# ========== NEW FUNCTIONS (add below) ==========

async def update_progress_message(message, current, total, live=0, dead=0, status="Checking"):
    """Update a Telegram message with a progress bar and stats."""
    percent = int((current / total) * 100) if total > 0 else 0
    bar = '█' * (percent // 10) + '░' * (10 - (percent // 10))
    text = (
        f"🔄 **{status}**\n"
        f"{bar} {percent}%\n\n"
        f"Checked: {current}/{total}\n"
        f"✅ Live: {live}\n"
        f"❌ Dead: {dead}"
    )
    try:
        await message.edit_text(text, parse_mode='Markdown')
    except Exception:
        # If editing fails (e.g., message deleted), just ignore
        pass

def format_bin_info(bin_prefix):
    """Fetch BIN info and return formatted string."""
    from utils.bin_utils import get_bin_info  # lazy import to avoid circular dependency
    info = get_bin_info(bin_prefix)
    if not info:
        return "⚠️ BIN lookup failed"
    lines = [
        f"**[+] Bin:** {bin_prefix}",
        f"**[+] Info:** {info['brand']} - {info['type']} - {info['category']}",
        f"**[+] Bank:** {info['bank']}",
        f"**[+] Country:** {info['country']} - {info['flag']}"
    ]
    return "\n".join(lines)