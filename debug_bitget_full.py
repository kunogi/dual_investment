import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 配置
PROXY = os.getenv("DEFAULT_PROXY")
PROXIES = {"http": PROXY, "https": PROXY} if PROXY else {}

COINS = {
    "BTC": 1,
    "ETH": 3,
    "SOL": 235
}

def bitget_full_scan(coin_name, p_id):
    """
    1. 先通过普通请求拿到所有可能的 settleDate
    2. 针对每个 settleDate 再次发起请求，精准抓取数据
    """
    base_url = "https://www.bitget.cloud/v1/finance/dualInvest/ordinary/product/list"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # ------------------- 第一步：扫描日期 -------------------
    print(f"\n🔍 [开始扫描] 币种: {coin_name} (ID: {p_id})")
    payload_scan = {
        "productTokenId": p_id,
        "tradeTokenId": 2, # 先以低买为例
        "direction": 0,
        "fromCalendar": False
    }

    try:
        resp = requests.post(base_url, json=payload_scan, headers=headers, proxies=PROXIES, timeout=10)
        scan_data = resp.json()
        
        if scan_data.get("code") != "200" or not scan_data.get("data"):
            print(f"❌ 无法获取日期分组列表")
            return

        # 提取所有 settleDate
        available_dates = [g.get("settleDate") for g in scan_data["data"] if g.get("settleDate")]
        print(f"📅 探测到 {len(available_dates)} 个潜在到期日: {[datetime.fromtimestamp(int(d)/1000).strftime('%m-%d') for d in available_dates]}")

        # ------------------- 第二步：针对日期暴力抓取 -------------------
        for ts in available_dates:
            d_str = datetime.fromtimestamp(int(ts)/1000).strftime('%m-%d')
            # 这里的参数 settleDate 是关键，强行指定日期
            payload_detail = {
                "productTokenId": p_id,
                "tradeTokenId": 2,
                "direction": 0,
                "settleDate": str(ts), # 强行传日期参数
                "fromCalendar": False
            }
            
            detail_resp = requests.post(base_url, json=payload_detail, headers=headers, proxies=PROXIES, timeout=10)
            detail_data = detail_resp.json()
            
            # 解析数据
            found_count = 0
            if detail_data.get("code") == "200" and detail_data.get("data"):
                for group in detail_data["data"]:
                    # 检查是否有 productList
                    p_list = group.get("productList", [])
                    if p_list:
                        found_count += len(p_list)
            
            if found_count > 0:
                print(f"✅ 日期 {d_str}: 成功抓取到 {found_count} 条产品!")
            else:
                print(f"⚠️ 日期 {d_str}: 依旧无数据 (即便指定了 settleDate)")

    except Exception as e:
        print(f"💥 异常: {e}")

if __name__ == "__main__":
    print("=== Bitget 多日期穿透探测器 ===")
    # 先以 ETH 和 BTC 为主进行测试
    bitget_full_scan("ETH", 3)
    bitget_full_scan("BTC", 1)