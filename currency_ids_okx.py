import requests
import time

def fetch_okx_currency_pairs():
    t = int(time.time() * 1000)
    url = f"https://www.okx.com/priapi/v2/sfp/dcd/currency-pair?containQuote=true&t={t}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.okx.com/",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            currency_pairs = data.get("data", {}).get("currencyPairs", [])
            print(f"✅ Found {len(currency_pairs)} groups\n")

            currency_to_id = {}
            for group in currency_pairs:
                pairs = group.get("currencyPairs", [])
                for p in pairs:
                    currency = p.get("currency")
                    currency_id = p.get("currencyId")
                    if currency and currency_id is not None:
                        currency_to_id[currency] = currency_id
                        print(f"  {currency}: {currency_id}")

            # 输出目标币种
            print("\n🔍 Target coins:")
            for target in ["BTC", "ETH", "SOL"]:
                print(f"  {target}: {currency_to_id.get(target, 'NOT FOUND')}")

            return currency_to_id
        else:
            print("❌ Failed:", response.text[:300])
    except Exception as e:
        print("⚠️ Error:", repr(e))
    return {}

if __name__ == "__main__":
    fetch_okx_currency_pairs()