# fetch_bitget_with_token.py
import requests
from datetime import datetime

def fetch_bitget_with_full_headers():
    url = "https://www.bitget.cloud/v1/finance/dualInvest/ordinary/product/list"

    # === 从你的 curl 复制的完整 headers + cookie ===
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
        # Cookie 合并进来
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

    # 请求体（从你的 curl --data-raw）
    payload = {
        "productTokenId": 3,
        "tradeTokenId": 2,
        "direction": 0,
        "timeRange": "",
        "settleDate": "",
        "fromCalendar": False
    }

    try:
        print("📡 使用完整 Token + Cookie 请求 Bitget...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"✅ 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "200":
                print("🎉 成功获取 Bitget 数据！")
                return data["data"]
            else:
                print(f"❌ API 错误: {data}")
        else:
            print(f"❌ HTTP 错误: {response.text[:300]}")
    except Exception as e:
        print(f"⚠️ 异常: {e}")
    return None

def main():
    raw_data = fetch_bitget_with_full_headers()
    if not raw_data:
        print("❌ 未能获取有效数据")
        return

    # 解析产品列表
    products = []
    for group in raw_data:
        settle_date = group["settleDate"]  # 毫秒时间戳
        for item in group["productList"]:
            try:
                products.append({
                    "strike": float(item["targetPrice"]),
                    "apy": float(item["apy"]),
                    "expiry_time": int(settle_date)
                })
            except (KeyError, ValueError, TypeError):
                continue

    # 排序：按到期时间升序 → 组内 APY 降序
    sorted_products = sorted(products, key=lambda x: (x["expiry_time"], -x["apy"]))

    def fmt_ts(ts_ms):
        return datetime.fromtimestamp(ts_ms // 1000).strftime("%m/%d %H:%M")

    print("\n📅 Bitget ETH 低买产品（使用浏览器 Token）")
    print(f"{'目标价':>8} | {'到期日':>10} | {'年化收益':>10}")
    print("-" * 38)
    for p in sorted_products:
        print(f"{p['strike']:>8.0f} | {fmt_ts(p['expiry_time']):>10} | {p['apy']:>10.2f}%")

if __name__ == "__main__":
    main()