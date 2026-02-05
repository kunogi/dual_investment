import streamlit as st
import pandas as pd
import requests
import time
import os
from datetime import datetime, date
from dotenv import load_dotenv
from curl_cffi import requests as requests_cffi

load_dotenv()

# --- 1. 强制铺满全屏 CSS 优化 ---
st.set_page_config(page_title="双币投资看板 Pro", layout="wide")

st.markdown("""
    <style>
    .block-container { padding: 1rem 1.5rem; max-width: 99% !important; }
    [data-testid="column"] { padding: 0px 8px !important; }
    .stTable { width: 100% !important; }
    td, th { padding: 3px 6px !important; font-size: 13.5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 国际化与配置 ---
LANG_DICT = {
    "zh": {
        "page_title": "双币投资看板 Pro", "sidebar_ctrl": "🎮 控制面板", "mode_toggle": "切换至【高卖】模式",
        "buy_low": "低买", "sell_high": "高卖", "asset_select": "选择币种:",
        "proxy_ctrl": "🌐 独立代理控制", "sync_btn": "⚡ 同步数据", "matrix_title": "📊 交易所对齐矩阵",
        "rank_title": "🏆 全网年化收益排行 (Top 30)", "target_price": "目标价", "dist_price": "距离%", "last_update": "⏱️ 最后更新:", "no_data": "⚠️ 未找到数据"
    },
    "en": {
        "page_title": "Dual Investment Pro", "sidebar_ctrl": "Dashboard Control", "mode_toggle": "Switch to SELL HIGH mode",
        "buy_low": "Buy Low", "sell_high": "Sell High", "asset_select": "Asset:",
        "proxy_ctrl": "Proxy Control", "sync_btn": "Sync Data", "matrix_title": "Alignment Matrix",
        "rank_title": "APY Rankings (Top 30)", "target_price": "Strike", "dist_price": "Dist.%", "last_update": "Last Updated:", "no_data": "No data found."
    }
}

if "lang" not in st.session_state: st.session_state.lang = "中文"
L = LANG_DICT["zh"] if st.session_state.lang == "中文" else LANG_DICT["en"]

COIN_CONFIG = {
    "BTC":  {"okx_id": 0,     "binance_symbol": "BTC",  "bitget_id": 1,   "gate_symbol": "BTC"},
    "ETH":  {"okx_id": 2,     "binance_symbol": "ETH",  "bitget_id": 3,   "gate_symbol": "ETH"},
    "SOL":  {"okx_id": 880,   "binance_symbol": "SOL",  "bitget_id": 235, "gate_symbol": "SOL"},
    "XAUT": {"okx_id": 140,   "binance_symbol": None,   "bitget_id": None, "gate_symbol": None},
}

env_proxy = os.getenv("DEFAULT_PROXY")
okx_auth = os.getenv("OKX_AUTH")
PROXY_SETTING = {"https": env_proxy, "http": env_proxy} if env_proxy else {}

# --- 3. 抓取引擎 ---

def get_live_prices(coin, use_proxy):
    proxies = PROXY_SETTING if use_proxy else {}
    try:
        r = requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={coin}-USDT", proxies=proxies, timeout=5).json()
        return float(r['data'][0]['last'])
    except: return 0

def get_okx(cfg, name, use_proxy, mode):
    c_id = cfg.get("okx_id")
    if c_id is None: return []
    
    # 核心修复：OKX 高卖/低买的参数对齐逻辑
    if mode == "Buy Low":
        opt_type = "PUT"
        inv_id = c_id  # 投资币种 ID (如 BTC 是 0)
        base_id = 7    # 结算币种 ID (USDT 是 7)
    else:
        opt_type = "CALL"
        inv_id = c_id
        base_id = 7    # 高卖通常也是以 USDT 结算，但 OKX 后端对 CALL 的映射有时不同

    url = f"https://www.okx.com/priapi/v2/sfp/dcd/products?currencyId={inv_id}&altCurrencyId={base_id}&dcdOptionType={opt_type}&t={int(time.time()*1000)}"
    
    headers = {
        "accept": "application/json", 
        "app-type": "web", 
        "referer": "https://www.okx.com/zh-hans/earn/dual",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 
        "authorization": okx_auth
    }
    
    proxies = PROXY_SETTING if use_proxy else {}
    try:
        resp = requests.get(url, headers=headers, timeout=10, proxies=proxies)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            products = data.get("products", [])
            # 如果 products 为空，尝试另一种 ID 组合（针对某些高卖对）
            if not products and mode == "Sell High":
                alt_url = f"https://www.okx.com/priapi/v2/sfp/dcd/products?currencyId=7&altCurrencyId={c_id}&dcdOptionType={opt_type}&t={int(time.time()*1000)}"
                resp = requests.get(alt_url, headers=headers, timeout=10, proxies=proxies)
                products = resp.json().get("data", {}).get("products", [])
            
            res = []
            for p in products:
                sk = p.get("strike")
                ay = p.get("annualYieldPercentage")
                if sk and ay:
                    res.append({
                        "coin": name, 
                        "strike": float(sk), 
                        "apy": float(ay), 
                        "expiry": int(p["expiryTime"]), 
                        "platform": "OKX"
                    })
            return res
    except Exception as e:
        print(f"OKX Error: {e}")
    return []

def get_bitget(cfg, name, use_proxy, mode):
    b_id = cfg.get("bitget_id")
    if b_id is None: return []
    url = "https://www.bitget.cloud/v1/finance/dualInvest/ordinary/product/list"
    direct, t_id = (0, 2) if mode == "Buy Low" else (1, 1)
    proxies = PROXY_SETTING if use_proxy else {}
    all_products = []
    try:
        r = requests.post(url, json={"productTokenId": b_id, "tradeTokenId": t_id, "direction": direct, "fromCalendar": False}, proxies=proxies, timeout=10).json()
        if r.get("code") == "200" and r.get("data"):
            dates = [g.get("settleDate") for g in r["data"] if g.get("settleDate")]
            for ts in dates:
                dr = requests.post(url, json={"productTokenId": b_id, "tradeTokenId": t_id, "direction": direct, "settleDate": str(ts), "fromCalendar": False}, proxies=proxies, timeout=10).json()
                if dr.get("code") == "200" and dr.get("data"):
                    for group in dr["data"]:
                        for p in group.get("productList", []):
                            all_products.append({"coin": name, "strike": float(p["targetPrice"]), "apy": float(p["apy"]), "expiry": int(ts), "platform": "Bitget"})
    except: pass
    return all_products

def get_binance(cfg, name, use_proxy, mode):
    if not cfg.get("binance_symbol"): return []
    p_type = "DOWN" if mode == "Buy Low" else "UP"
    i_asset = "USDT" if mode == "Buy Low" else cfg["binance_symbol"]
    t_asset = cfg["binance_symbol"] if mode == "Buy Low" else "USDT"
    url = "https://www.binance.com/bapi/earn/v5/friendly/pos/dc/project/list"
    params = {"investmentAsset": i_asset, "targetAsset": t_asset, "projectType": p_type, "pageSize": 100}
    proxies = PROXY_SETTING if use_proxy else {}
    try:
        r = requests.get(url, params=params, timeout=10, proxies=proxies).json()
        return [{"coin": name, "strike": float(i["strikePrice"]), "apy": float(i["apr"]) * 100, "expiry": int(i["settleTime"]), "platform": "Binance"} for i in r.get("data", {}).get("list", [])]
    except: return []

def get_gate(cfg, name, use_proxy, mode):
    symbol = cfg.get("gate_symbol")
    if not symbol: return []
    gate_type = "put" if mode == "Buy Low" else "call"
    url = f"https://www.gate.com/apiw/v2/earn/dual/project-list?coin={symbol}&type={gate_type}"
    proxies = PROXY_SETTING if use_proxy else {}
    try:
        resp = requests_cffi.get(url, impersonate="edge101", proxies=proxies, timeout=10)
        if resp.status_code == 200:
            res = []
            for i in resp.json().get("data", []):
                if int(i.get("min_vip_level", 0)) > 0: continue
                strike = i.get("exercise_price") or i.get("strike_price")
                apy_val = float(i.get("apy_display") or 0) * 100
                expiry_val = (i.get("delivery_timest") or i.get("end_timest")) * 1000
                if strike and apy_val > 0:
                    res.append({"coin": name, "strike": float(strike), "apy": apy_val, "expiry": int(expiry_val), "platform": "Gate"})
            return res
    except: pass
    return []

# --- 4. 侧边栏 ---
with st.sidebar:
    st.session_state.lang = st.selectbox("🌐 Language", ["中文", "English"], index=0 if st.session_state.lang == "中文" else 1)
    L = LANG_DICT["zh"] if st.session_state.lang == "中文" else LANG_DICT["en"]
    st.header(L["sidebar_ctrl"])
    invest_mode = st.toggle(L["mode_toggle"], value=False)
    mode_key = "Sell High" if invest_mode else "Buy Low"
    target_coin = st.radio(L["asset_select"], list(COIN_CONFIG.keys()) + ["Hybrid Dashboard"])
    st.subheader(L["proxy_ctrl"])
    p_bin, p_okx, p_bit, p_gate = st.checkbox("Binance Proxy", True), st.checkbox("OKX Proxy", True), st.checkbox("Bitget Proxy", True), st.checkbox("Gate Proxy", True)
    st.button(L["sync_btn"], type="primary", width="stretch")

# --- 5. 数据处理 ---
all_data, current_prices = [], {}
items = COIN_CONFIG.items() if "Hybrid" in target_coin else [(target_coin, COIN_CONFIG[target_coin])]

with st.spinner("🚀 同步中..."):
    for name, cfg in items:
        price = get_live_prices(name, p_okx)
        current_prices[name] = price
        all_data += get_okx(cfg, name, p_okx, mode_key)
        all_data += get_bitget(cfg, name, p_bit, mode_key)
        all_data += get_binance(cfg, name, p_bin, mode_key)
        all_data += get_gate(cfg, name, p_gate, mode_key)

if not all_data:
    st.warning(L["no_data"])
else:
    df = pd.DataFrame(all_data)
    df['expiry_date'] = df['expiry'].apply(lambda x: date.fromtimestamp(x // 1000))
    dist_col = L["dist_price"]
    df[dist_col] = df.apply(lambda r: ((r['strike'] - current_prices.get(r['coin'], 0)) / (current_prices.get(r['coin']) or 1)) * 100, axis=1).round(1)
    df['display_name'] = df.apply(lambda r: f"{r['coin']}-{r['expiry_date'].strftime('%m%d')}", axis=1)

    st.title(L["page_title"])
    st.caption(f"{L['last_update']} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    col_left, col_right = st.columns([1.35, 0.65])
    
    with col_left:
        st.subheader(L["matrix_title"])
        for exp_date in sorted(df['expiry_date'].unique()):
            st.write(f"📅 **{exp_date.strftime('%m/%d')}**")
            sub = df[df['expiry_date'] == exp_date].copy()
            pivot = sub.pivot_table(index=['coin', 'strike', dist_col], columns='platform', values='apy', aggfunc='max').reindex(columns=['Binance', 'OKX', 'Bitget', 'Gate'])
            pivot['max_val'] = pivot.max(axis=1)
            pivot = pivot.sort_values('max_val', ascending=False).drop(columns=['max_val'])
            st.dataframe(pivot.style.highlight_max(axis=1, color="#1e4620").format("{:.1f}%", na_rep="--"), width="stretch")

    with col_right:
        st.subheader(L["rank_title"])
        rank_df = df.sort_values("apy", ascending=False).head(30)
        
        # --- 彻底去掉索引列的关键操作 ---
        display_rank = rank_df[['display_name', 'platform', 'apy', 'strike']].copy()
        display_rank.columns = ['Asset', 'Ex', 'APY', L['target_price']]
        display_rank['APY'] = display_rank['APY'].apply(lambda x: f"{x:.1f}%")
        display_rank[L['target_price']] = display_rank[L['target_price']].apply(lambda x: f"{x:g}")
        
        # 将 'Asset' 设为索引，st.table 就会以它为第一列，且不再显示那列奇怪的数字
        display_rank.set_index('Asset', inplace=True)
        
        st.table(display_rank)