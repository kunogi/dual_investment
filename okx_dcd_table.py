import requests
import time
from datetime import datetime

# OKX 币种映射
OKX_CURRENCY_MAP = {
    "BTC": 0,
    "ETH": 2,
    "XAUT": 16789,
}

def fetch_okx_products(coin, currency_id):
    t = int(time.time() * 1000)
    url = f"https://www.okx.com/priapi/v2/sfp/dcd/products?currencyId={currency_id}&altCurrencyId=7&dcdOptionType=PUT&t={t}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.okx.com/",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("products", [])
            print(f"✅ {coin}: 共 {len(products)} 个产品\n")

            # 过滤并排序
            valid = []
            for p in products:
                strike = p.get("strike")
                apy = p.get("annualYieldPercentage")
                expiry_time = p.get("expiryTime")
                if not strike or not apy or not expiry_time:
                    continue
                valid.append({
                    "strike": float(strike),
                    "apy": float(apy),
                    "expiry_time": expiry_time,
                    "expiry_str": datetime.fromtimestamp(expiry_time // 1000).strftime("%Y/%m/%d %H:%M")
                })

            # 排序：先到期时间升序，再 APY 降序
            sorted_products = sorted(
                valid,
                key=lambda x: (x["expiry_time"], -x["apy"])
            )

            # 输出表格
            print(f"=== {coin} 低买（看跌）产品列表 ===")
            print(f"{'目标价':>10} | {'到期日':>12} | {'年化收益率':>10}")
            print("-" * 40)
            for p in sorted_products[:15]:  # 显示前15条
                print(f"{p['strike']:>10.0f} | {p['expiry_str']:<12} | {p['apy']:>10.2f}%")
            print()

            return sorted_products
        else:
            print(f"❌ {coin}: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ {coin} error: {repr(e)}")
    return []

if __name__ == "__main__":
    for coin in ["BTC", "ETH", "XAUT"]:
        fetch_okx_products(coin, OKX_CURRENCY_MAP[coin])