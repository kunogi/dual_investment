import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
auth = os.getenv("OKX_AUTH")
proxy = os.getenv("DEFAULT_PROXY")

def fetch_okx_simple():
    # 2. 目标 URL (使用你 curl 中成功的参数)
    url = "https://www.okx.com/priapi/v2/sfp/dcd/products"
    params = {
        "currencyId": "2",
        "altCurrencyId": "7",
        "dcdOptionType": "CALL"
    }

    # 3. 核心 Headers (从你的 curl 命令中提取)
    headers = {
        "accept": "application/json",
        "app-type": "web",
        "referer": "https://www.okx.com/zh-hans/earn/dual",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "authorization": auth}

    print(f"📡 发起请求...")

    try:
        # 使用 Session 以保持状态
        session = requests.Session()
        proxies_dict = {
            "http": proxy,
            "https": proxy
        }
        resp = session.get(url, params=params, headers=headers, proxies=proxies_dict, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("data", {}).get("products", [])
            print(f"✅ 抓取成功！获取到 {len(products)} 个 ETH 产品")
            if products:
                print(f"📈 示例产品：目标价 {products[0].get('strike')}, 年化 {products[0].get('annualYieldPercentage')}%")
        else:
            print(f"❌ 失败，状态码: {resp.status_code}")
            print(f"🔍 响应体: {resp.text[:200]}")
            
    except Exception as e:
        print(f"⚠️ 报错: {str(e)}")

if __name__ == "__main__":
    fetch_okx_simple()