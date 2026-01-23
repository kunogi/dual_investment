import requests
import time
from datetime import datetime

PROXIES = {"https": "http://127.0.0.1:7897"}

def fetch_binance_dcd(coin="ETH"):
    url = "https://www.binance.com/bapi/earn/v5/friendly/pos/dc/project/list"
    params = {
        "investmentAsset": "USDT",
        "targetAsset": coin,
        "projectType": "DOWN",  # 低买（看跌）
        "sortType": "APY_DESC",
        "pageIndex": 1,
        "pageSize": 50,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.binance.com/",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, params=params, headers=headers, proxies=PROXIES, timeout=10)
        if response.status_code == 200:
            data = response.json()
            projects = data.get("data", {}).get("list", [])
            print(f"✅ {coin}: 共 {len(projects)} 个产品\n")

            valid = []
            for p in projects:
                strike_price = p.get("strikePrice")
                settle_time = p.get("settleTime")  # 字符串
                apr = p.get("apr")  # 字符串，如 "1.8216"

                if not strike_price or not settle_time or not apr:
                    continue

                try:
                    strike = float(strike_price)
                    apy = float(apr) * 100  # ← 关键：乘以 100
                    settle_ts = int(settle_time)
                    settle_str = datetime.fromtimestamp(settle_ts // 1000).strftime("%Y/%m/%d %H:%M")
                except (ValueError, TypeError):
                    continue

                valid.append({
                    "strike": strike,
                    "apy": apy,
                    "settle_time": settle_ts,
                    "settle_str": settle_str
                })

            # 排序：先到期时间升序，再 APY 降序
            sorted_projects = sorted(
                valid,
                key=lambda x: (x["settle_time"], -x["apy"])
            )

            print(f"=== {coin} 低买（看跌）产品列表 ===")
            print(f"{'目标价':>10} | {'到期日':>12} | {'年化收益率':>10}")
            print("-" * 40)
            for p in sorted_projects[:15]:
                print(f"{p['strike']:>10.0f} | {p['settle_str']:<12} | {p['apy']:>10.2f}%")
            print()

            return sorted_projects
        else:
            print(f"❌ {coin}: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ {coin} error: {repr(e)}")
    return []

if __name__ == "__main__":
    fetch_binance_dcd("ETH")