import requests
import json

# Configuration
PROXY_PORT = 7897
PROXIES = {
    "http": f"http://127.0.0.1:{PROXY_PORT}",
    "https": f"http://127.0.0.1:{PROXY_PORT}",
}

COINS = ["BTC", "ETH", "SOL", "DOGE", "XAUT"]

def fetch_prices(coin):
    results = {"Coin": coin}
    print(f"🔍 Fetching real-time prices for {coin}...")

    # 1. Binance (Ticker API)
    try:
        if coin == "XAUT":
            results["Binance"] = "N/A (Not Listed)"
        else:
            bn_url = f"https://api.binance.com/api/v3/ticker/price?symbol={coin}USDT"
            bn_res = requests.get(bn_url, proxies=PROXIES, timeout=5).json()
            results["Binance"] = f"{float(bn_res['price']):,.2f}"
    except Exception as e:
        results["Binance"] = f"Error: {type(e).__name__}"

    # 2. OKX (V5 Public API)
    try:
        # OKX uses dash separator: BTC-USDT
        ok_url = f"https://www.okx.com/api/v5/market/ticker?instId={coin}-USDT"
        ok_res = requests.get(ok_url, proxies=PROXIES, timeout=5).json()
        if ok_res.get("data"):
            results["OKX"] = f"{float(ok_res['data'][0]['last']):,.2f}"
        else:
            results["OKX"] = "No Data"
    except Exception as e:
        results["OKX"] = f"Error: {type(e).__name__}"

    # 3. Bitget (V2 Spot API)
    try:
        if coin == "XAUT":
             results["Bitget"] = "N/A (Not Listed)"
        else:
            # Bitget uses BTCUSDT
            bg_url = f"https://api.bitget.com/api/v2/spot/market/tickers?symbol={coin}USDT"
            bg_res = requests.get(bg_url, proxies=PROXIES, timeout=5).json()
            if bg_res.get("data") and len(bg_res["data"]) > 0:
                results["Bitget"] = f"{float(bg_res['data'][0]['lastPr']):,.2f}"
            else:
                results["Bitget"] = "No Data"
    except Exception as e:
        results["Bitget"] = f"Error: {type(e).__name__}"

    return results

if __name__ == "__main__":
    print(f"🚀 Starting Price Verification (Proxy: 127.0.0.1:{PROXY_PORT})\n" + "="*50)
    
    table_data = []
    for coin in COINS:
        data = fetch_prices(coin)
        table_data.append(data)
        
    # Print formatted results
    print("\n" + "="*70)
    print(f"{'Coin':<8} | {'Binance':<15} | {'OKX':<15} | {'Bitget':<15}")
    print("-" * 70)
    for row in table_data:
        print(f"{row['Coin']:<8} | {row['Binance']:<15} | {row['OKX']:<15} | {row['Bitget']:<15}")
    print("="*70)