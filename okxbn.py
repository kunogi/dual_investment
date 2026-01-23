import requests
import time
from datetime import datetime
from collections import defaultdict

# ===== 代理设置（根据你的环境）=====
USE_PROXY = True
PROXIES = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"} if USE_PROXY else None

# ========================
# 1. OKX - 完全使用你提供的代码
# ========================
OKX_CURRENCY_MAP = {"BTC": 0, "ETH": 2, "SOL": 880}

def fetch_okx_products(coin="ETH"):
    currency_id = OKX_CURRENCY_MAP.get(coin)
    if currency_id is None:
        return []
    t = int(time.time() * 1000)
    url = f"https://www.okx.com/priapi/v2/sfp/dcd/products?currencyId={currency_id}&altCurrencyId=7&dcdOptionType=PUT&t={t}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.okx.com/",
        "Accept": "application/json",
    }
    try:
        response = requests.get(url, headers=headers, proxies=PROXIES, timeout=10)
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("products", [])
            result = []
            for p in products:
                strike = p.get("strike")
                apy = p.get("annualYieldPercentage")
                expiry_time = p.get("expiryTime")  # 毫秒时间戳
                if strike and apy and expiry_time:
                    result.append({
                        "strike": float(strike),
                        "apy": float(apy),
                        "expiry_time": expiry_time
                    })
            return result
    except Exception as e:
        print(f"⚠️ OKX {coin} error: {e}")
    return []

# ========================
# 2. Binance - 完全使用你提供的代码
# ========================
def fetch_binance_dcd(coin="ETH"):
    url = "https://www.binance.com/bapi/earn/v5/friendly/pos/dc/project/list"
    params = {
        "investmentAsset": "USDT",
        "targetAsset": coin,
        "projectType": "DOWN",
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
            result = []
            for p in projects:
                strike_price = p.get("strikePrice")
                settle_time = p.get("settleTime")  # 字符串，毫秒
                apr = p.get("apr")  # 小数字符串，如 "1.8216"

                if not strike_price or not settle_time or not apr:
                    continue

                try:
                    strike = float(strike_price)
                    apy = float(apr) * 100  # 转为百分比
                    settle_ts = int(settle_time)
                    result.append({
                        "strike": strike,
                        "apy": apy,
                        "expiry_time": settle_ts
                    })
                except (ValueError, TypeError):
                    continue
            return result
    except Exception as e:
        print(f"⚠️ Binance {coin} error: {e}")
    return []

# ========================
# 3. 对比主逻辑
# ========================
def main():
    print("🔍 正在抓取 OKX + Binance ETH 低买产品...\n")

    okx_data = fetch_okx_products("ETH")
    binance_data = fetch_binance_dcd("ETH")

    if not okx_data and not binance_data:
        print("❌ 两个平台均无数据")
        return

    # 收集所有到期时间（毫秒）
    all_expiry = set(p["expiry_time"] for p in (okx_data + binance_data))
    grouped = defaultdict(lambda: defaultdict(dict))

    # 填入 OKX
    for p in okx_data:
        # 四舍五入到最近的 25 美元（对齐报价）
        strike_rounded = round(p["strike"] / 25) * 25
        grouped[p["expiry_time"]][strike_rounded]["okx"] = p["apy"]

    # 填入 Binance
    for p in binance_data:
        strike_rounded = round(p["strike"] / 25) * 25
        grouped[p["expiry_time"]][strike_rounded]["binance"] = p["apy"]

    def fmt_ts(ts_ms):
        return datetime.fromtimestamp(ts_ms // 1000).strftime("%m/%d %H:%M")

    def fmt_apy(apy):
        return f"{apy:>9.2f}%" if apy is not None else "       --"

    # 按到期时间排序输出
    for expiry in sorted(grouped.keys()):
        products = grouped[expiry]
        if not products:
            continue

        print(f"\n📅 到期时间: {fmt_ts(expiry)}")
        print("-" * 46)
        print(f"{'目标价':>8} | {'OKX':>10} | {'Binance':>10}")
        print("-" * 46)

        for strike in sorted(products.keys()):
            r = products[strike]
            okx_apy = r.get("okx")
            binance_apy = r.get("binance")
            print(f"{strike:>8.0f} | {fmt_apy(okx_apy)} | {fmt_apy(binance_apy)}")

if __name__ == "__main__":
    main()