# dual_compare.py
import requests
import time
from datetime import datetime
from collections import defaultdict

# ========== 代理配置 ==========
PROXIES = {"https": "http://127.0.0.1:7897"}

# ========== OKX 抓取（保持原样）==========
OKX_CURRENCY_MAP = {
    "BTC": 0,
    "ETH": 2,
    "SOL": 880,
}

def fetch_okx_products_for_merge(coin, currency_id):
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
                    "platform": "okx"
                })
            return valid
        else:
            print(f"❌ OKX {coin}: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ OKX {coin} error: {repr(e)}")
    return []

# ========== Binance 抓取（完全使用你提供的正确接口）==========
def fetch_binance_products_for_merge():
    url = "https://www.binance.com/bapi/earn/v5/friendly/pos/dc/project/list"
    params = {
        "investmentAsset": "USDT",
        "targetAsset": "ETH",
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
        resp = requests.get(url, params=params, headers=headers, proxies=PROXIES, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            products = []
            for item in data.get("data", {}).get("list", []):
                strike_price = item.get("strikePrice")
                settle_time = item.get("settleTime")
                apr = item.get("apr")
                if strike_price and settle_time and apr:
                    try:
                        products.append({
                            "strike": float(strike_price),
                            "apy": float(apr) * 100,
                            "expiry_time": int(settle_time),
                            "platform": "binance"
                        })
                    except (ValueError, TypeError):
                        continue
            return products
        else:
            print(f"❌ Binance HTTP {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Binance error: {e}")
    return []

# ========== Bitget 抓取（完全使用你最初给的原始逻辑）==========
def fetch_bitget_products_for_merge():
    url = "https://www.bitget.cloud/v1/finance/dualInvest/ordinary/product/list"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json;charset=UTF-8",
        "custom-token": "huZcIVC8q1pmfV4DE7qsOcE2z0ZmfuZNIuO7k0ZXdVOjfDBsOVZXIDOiz",
        "deviceid": "6f75294e1ecf7aacf270732166d759a5",
        "dy-token": "69722650IIH4f43v9AgKP8qYL9PMgR6Wvl3IciP1",
        "language": "zh_CN",
        "locale": "zh_CN",
        "origin": "https://www.bitget.cloud",
        "priority": "u=1, i",
        "referer": "https://www.bitget.cloud/zh-CN/earning/dual-investment",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "terminalcode": "0aef4bab530da086608ca75ffee4f1b6",
        "terminaltype": "1",
        "tm": "1769088848560",
        "uhti": "w1769088849946225606143ca",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "cookie": (
            "theme=white; "
            "fingerprint-1769078017462-1509.7000000476837-0.4856549390017484=true; "
            "terminalCode-1769078017463-1510.8000000715256-0.8083878590851277=true; "
            "_dx_kvani5r=13b5a038dbca23ed259e82e4ea4acdca1dce5185ab010ffb1600a5e32573cf5afdff9ab1; "
            "4ef1398a95037d16=txrTIx9wF7l%2F4cy%2Bu3xgTt1dDxPZJEjTebFFh%2FB5C5HvfzVEGAGGLKkyLkl%2FjeqqjWnP3v8RgaAMEiS5S8ItmyMZEB424AQa06SfBtewHRbKkFv4SbSajJaNg0vA%2FqrT7RuxOISzrccDzKWRwYB2lmig9jxxyd5JbwKZW0itbcODipEQYOxDmu4V55x5YyWc; "
            "OptanonAlertBoxClosed=Thu%20Jan%2022%202026%2018:33:44%20GMT+0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4); "
            "OptanonConsent=isMarketing=1&isStatistic=1; "
            "_cfuvid=wuGulYWIpQmHuWo5YM1HmFJlTtazj2tGQ.wR9Y6DjN0-1769078078798-0.0.1.1-604800000; "
            "_TDID_CK=1769078080016; "
            "BITGET_LOCAL_COOKIE={%22bitget_lang%22:%22zh-CN%22%2C%22bitget_unit%22:%22TWD%22%2C%22bitget_currency%22:%22%22%2C%22bitget_showasset%22:false%2C%22bitget_theme%22:%22dark%22%2C%22bitget_layout%22:%22right%22%2C%22bitget_valuationunit%22:0%2C%22bitget_valuationunitandfiat%22:0%2C%22bitgt_login%22:false%2C%22bitget_valuationunit_new%22:1}; "
            "__cf_bm=Pi5ZtR2mt_1_N1E8JB.pmtKpEUj41PoGUQTzgDVarJo-1769088130-1.0.1.1-S6eK6nUz.tGsOb.vr_OQjrJcE9Ln60oYrGwp9ba.hP3CA8DDEsAx1CNvN0Y9qxuDSDV4tknMBBCkVaL1Pj2Na4ovUmevbFVCiw8JO1layrg; "
            "dy_token=69722650IIH4f43v9AgKP8qYL9PMgR6Wvl3IciP1"
        )
    }
    payload = {
        "productTokenId": 3,
        "tradeTokenId": 2,
        "direction": 0,
        "timeRange": "",
        "settleDate": "",
        "fromCalendar": False
    }
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=PROXIES, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "200":
                products = []
                for group in data["data"]:
                    settle_date = group["settleDate"]
                    for item in group.get("productList", []):
                        try:
                            products.append({
                                "strike": float(item["targetPrice"]),
                                "apy": float(item["apy"]),
                                "expiry_time": int(settle_date),
                                "platform": "bitget"
                            })
                        except (KeyError, ValueError, TypeError):
                            continue
                return products
    except Exception as e:
        print(f"⚠️ Bitget error: {e}")
    return []

# ========== 辅助函数（仅用于格式化输出）==========
def align_strike(strike):
    return round(strike / 25) * 25

def fmt_ts(ts_ms):
    dt = datetime.fromtimestamp(ts_ms // 1000)
    return dt.strftime("%m/%d %H:%M")

def fmt_apy(apy, is_max=False):
    if apy is None:
        return "       --"
    color = "\033[92m" if is_max else ""
    reset = "\033[0m" if is_max else ""
    return f"{color}{apy:>9.2f}%{reset}"

# ========== 主程序 ==========
def main():
    print("🔍 正在抓取三平台 ETH 低买产品...\n")
    time.sleep(0.3)

    okx_products = fetch_okx_products_for_merge("ETH", OKX_CURRENCY_MAP["ETH"])
    binance_products = fetch_binance_products_for_merge()
    bitget_products = fetch_bitget_products_for_merge()

    all_products = okx_products + binance_products + bitget_products

    if not all_products:
        print("❌ 所有平台均无数据")
        return

    grouped = defaultdict(lambda: defaultdict(dict))
    for item in all_products:
        strike = align_strike(item["strike"])
        platform = item["platform"]
        apy = item["apy"]
        expiry = item["expiry_time"]
        grouped[expiry][strike][platform] = apy

    print("\n============================================================")
    print("📊 三平台 ETH 低买产品对比（目标价已对齐到 25 的倍数）")
    print("============================================================")

    for expiry in sorted(grouped.keys()):
        products = grouped[expiry]
        print(f"\n📅 到期时间: {fmt_ts(expiry)}")
        print("-" * 62)
        print(f"{'目标价':>8} | {'OKX':>10} | {'Binance':>10} | {'Bitget':>10}")
        print("-" * 62)

        items = list(products.items())
        def sort_key(item):
            strike, apys = item
            max_apy = max(
                apys.get("okx", -1),
                apys.get("binance", -1),
                apys.get("bitget", -1)
            )
            return (-max_apy, -strike)
        sorted_items = sorted(items, key=sort_key)

        for strike, apys in sorted_items:
            okx_apy = apys.get("okx")
            binance_apy = apys.get("binance")
            bitget_apy = apys.get("bitget")
            valid_apys = [x for x in [okx_apy, binance_apy, bitget_apy] if x is not None]
            if not valid_apys:
                continue
            max_in_row = max(valid_apys)
            okx_str = fmt_apy(okx_apy, okx_apy == max_in_row)
            binance_str = fmt_apy(binance_apy, binance_apy == max_in_row)
            bitget_str = fmt_apy(bitget_apy, bitget_apy == max_in_row)
            print(f"{strike:>8.0f} | {okx_str} | {binance_str} | {bitget_str}")

if __name__ == "__main__":
    main()