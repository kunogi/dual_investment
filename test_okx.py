import requests
import time
import json
from datetime import datetime

# 调试配置
TARGET_COIN = "BTC"
COIN_ID = 0  # BTC 在 OKX 的 ID
USDT_ID = 7  # USDT 在 OKX 的 ID

def test_call(name, params):
    url = "https://www.okx.com/priapi/v2/sfp/dcd/products"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.okx.com/earn/dual",
        "Accept": "application/json",
    }
    
    print(f"--- 正在测试方案: {name} ---")
    print(f"请求参数: {params}")
    
    try:
        # 为了排除缓存干扰，每次使用全新的 Session
        with requests.Session() as s:
            resp = s.get(url, params=params, headers=headers, timeout=10)
            print(f"HTTP 状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("data", {}).get("products", [])
                print(f"📊 返回产品数量: {len(products)}")
                if len(products) > 0:
                    first = products[0]
                    print(f"✅ 成功获取数据！第一个产品: 目标价 {first.get('strike')}, 年化 {first.get('annualYieldPercentage')}%")
                else:
                    print("❌ 返回成功但产品列表为空。")
            else:
                print(f"❌ 请求失败，返回内容: {resp.text[:100]}")
    except Exception as e:
        print(f"⚠️ 发生异常: {repr(e)}")
    print("\n")

if __name__ == "__main__":
    t = int(time.time() * 1000)

    # 方案 1: 你的测试脚本成功的模式 (如果这在低买下不行，那说明 ID 必须换位)
    # 这对应你说的：高卖有数据
    test_call("1. 高卖模式 (SELL HIGH)", {
        "currencyId": COIN_ID,
        "altCurrencyId": USDT_ID,
        "dcdOptionType": "CALL",
        "t": t
    })

    # 方案 2: 我们之前尝试的低买模式 (可能因为缺少 indexCurrencyId 失败)
    test_call("2. 基础低买模式 (BUY LOW - Basic)", {
        "currencyId": USDT_ID,
        "altCurrencyId": COIN_ID,
        "dcdOptionType": "PUT",
        "t": t + 1
    })

    # 方案 3: 强制对齐 Web 端逻辑 (加入 indexCurrencyId)
    test_call("3. Web端模拟低买 (BUY LOW - with IndexID)", {
        "currencyId": USDT_ID,
        "altCurrencyId": COIN_ID,
        "indexCurrencyId": COIN_ID,
        "dcdOptionType": "PUT",
        "t": t + 2
    })

    # 方案 4: 极端测试 - 交换 ID 顺序但保持 PUT
    test_call("4. 交换ID顺序的低买 (BUY LOW - Swapped IDs)", {
        "currencyId": COIN_ID,
        "altCurrencyId": USDT_ID,
        "dcdOptionType": "PUT",
        "t": t + 3
    })