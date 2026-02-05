from curl_cffi import requests
import os

def test_gate_ultra():
    # 模拟 Edge 120 的 TLS 指纹
    # 这一行是关键，requests 库做不到这一点
    resp = requests.get(
        "https://www.gate.com/apiw/v2/earn/dual/project-list?coin=ETH&type=put",
        impersonate="edge101", # 伪装成浏览器
        proxies={"http": "http://127.0.0.1:10808", "https": "http://127.0.0.1:10808"},
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "accept": "application/json"
        }
    )
    print(resp.json())

if __name__ == "__main__":
    test_gate_ultra()