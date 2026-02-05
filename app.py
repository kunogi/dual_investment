import streamlit as st
import pandas as pd
import requests
import time
import os
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# --- 1. 国际化字典 ---
LANG_DICT = {
    "zh": {
        "page_title": "双币投资看板 Pro",
        "sidebar_ctrl": "🎮 控制面板",
        "mode_toggle": "切换至【高卖】模式",
        "buy_low": "低买",
        "sell_high": "高卖",
        "current_strat": "当前策略",
        "asset_select": "选择币种:",
        "proxy_ctrl": "🌐 代理控制",
        "sync_btn": "⚡ 同步数据",
        "matrix_title": "📊 交易所对齐看板 (按收益率降序)",
        "rank_title": "🏆 全网年化收益排行 (Top 30)",
        "settlement": "结算时间",
        "target_price": "目标价",
        "dist_price": "距离%",
        "last_update": "⏱️ 数据最后更新时间:",
        "no_data": "⚠️ 未找到数据，请检查代理或配置"
    },
    "en": {
        "page_title": "Dual Investment Pro",
        "sidebar_ctrl": "🎮 Dashboard Control",
        "mode_toggle": "Switch to SELL HIGH mode",
        "buy_low": "Buy Low",
        "sell_high": "Sell High",
        "current_strat": "Strategy",
        "asset_select": "Asset:",
        "proxy_ctrl": "🌐 Proxy Control",
        "sync_btn": "⚡ Sync Data",
        "matrix_title": "📊 Alignment Matrix (Sorted by APY)",
        "rank_title": "🏆 APY Rankings (Top 30)",
        "settlement": "Expiry",
        "target_price": "Strike",
        "dist_price": "Dist.%",
        "last_update": "⏱️ Last Updated:",
        "no_data": "⚠️ No data found. Check Proxy/Config."
    }
}

# --- 2. 页面配置 ---
st.set_page_config(page_title="Dual Investment Pro", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "中文"

COIN_CONFIG = {
    "BTC":  {"okx_id": 0,     "binance_symbol": "BTC",  "bitget_id": 2},
    "ETH":  {"okx_id": 2,     "binance_symbol": "ETH",  "bitget_id": 3},
    "SOL":  {"okx_id": 880,   "binance_symbol": "SOL",  "bitget_id": 235},
    # "DOGE": {"okx_id": 1054,  "binance_symbol": "DOGE", "bitget_id": 82},
    "XAUT": {"okx_id": 16789, "binance_symbol": None,   "bitget_id": None}
}

env_proxy = os.getenv("DEFAULT_PROXY")
PROXY_SETTING = {"https": env_proxy, "http": env_proxy} if env_proxy else {}

# --- 3. 核心引擎 ---

def get_live_prices(coin, use_proxy):
    prices = []
    proxies = PROXY_SETTING if use_proxy else {}
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin}USDT", proxies=proxies, timeout=3).json()
        prices.append(float(r['price']))
    except: pass
    try:
        r = requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={coin}-USDT", proxies=proxies, timeout=3).json()
        prices.append(float(r['data'][0]['last']))
    except: pass
    return sum(prices)/len(prices) if prices else 0

def get_okx(cfg, name, use_proxy, mode):
    if cfg.get("okx_id") is None: return []
    t = int(time.time() * 1000)
    curr_id = cfg['okx_id']
    alt_id = 7
    opt_type = "PUT" if mode == "Buy Low" else "CALL"
    url = f"https://www.okx.com/priapi/v2/sfp/dcd/products?currencyId={curr_id}&altCurrencyId={alt_id}&dcdOptionType={opt_type}&t={t}"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.okx.com/", "Accept": "application/json"}
    proxies = PROXY_SETTING if use_proxy else {}
    try:
        resp = requests.get(url, headers=headers, timeout=10, proxies=proxies)
        if resp.status_code == 200:
            products = resp.json().get("data", {}).get("products", [])
            return [{"coin": name, "strike": float(p["strike"]), "apy": float(p["annualYieldPercentage"]), "expiry": int(p["expiryTime"]), "platform": "OKX"} 
                    for p in products if p.get("strike") and p.get("annualYieldPercentage")]
    except: pass
    return []

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

def get_bitget(cfg, name, use_proxy, mode):
    if not cfg.get("bitget_id"): return []
    direct = 0 if mode == "Buy Low" else 1
    url = "https://www.bitget.cloud/v1/finance/dualInvest/ordinary/product/list"
    proxies = PROXY_SETTING if use_proxy else {}
    try:
        r = requests.post(url, json={"productTokenId": cfg["bitget_id"], "tradeTokenId": 2, "direction": direct}, timeout=10, proxies=proxies).json()
        res = []
        if r.get("code") == "200":
            for g in r["data"]:
                for p in g.get("productList", []):
                    res.append({"coin": name, "strike": float(p["targetPrice"]), "apy": float(p["apy"]), "expiry": int(g["settleDate"]), "platform": "Bitget"})
        return res
    except: return []

# --- 4. UI 侧边栏 ---
with st.sidebar:
    st.session_state.lang = st.selectbox("🌐 Language", ["中文", "English"], index=0 if st.session_state.lang == "中文" else 1)
    L = LANG_DICT["zh"] if st.session_state.lang == "中文" else LANG_DICT["en"]
    
    st.header(L["sidebar_ctrl"])
    invest_mode = st.toggle(L["mode_toggle"], value=False)
    mode_key = "Sell High" if invest_mode else "Buy Low"
    st.info(f"{L['current_strat']}: **{L['sell_high'] if invest_mode else L['buy_low']}**")
    
    target = st.radio(L["asset_select"], list(COIN_CONFIG.keys()) + ["Hybrid Dashboard"])
    
    st.subheader(L["proxy_ctrl"])
    p_okx = st.checkbox("OKX Proxy", value=True)
    p_bin = st.checkbox("Binance Proxy", value=True)
    p_bit = st.checkbox("Bitget Proxy", value=True)
    
    st.button(L["sync_btn"], type="primary", use_container_width=True)

# --- 5. 主内容渲染 ---
st.title(L["page_title"])
st.caption(f"{L['last_update']} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

current_prices = {}
if target != "Hybrid Dashboard":
    p = get_live_prices(target, p_okx)
    current_prices[target] = p
    st.subheader(f"{target} Price: ${p:,.2f}")
else:
    for c in COIN_CONFIG: current_prices[c] = get_live_prices(c, p_okx)

all_data = []
with st.spinner("Syncing yields..."):
    items = COIN_CONFIG.items() if target == "Hybrid Dashboard" else [(target, COIN_CONFIG[target])]
    for name, cfg in items:
        all_data += get_okx(cfg, name, p_okx, mode_key)
        all_data += get_binance(cfg, name, p_bin, mode_key)
        all_data += get_bitget(cfg, name, p_bit, mode_key)

if not all_data:
    st.warning(L["no_data"])
else:
    df = pd.DataFrame(all_data)
    dist_col = L["dist_price"]
    df[dist_col] = df.apply(lambda r: ((r['strike'] - current_prices.get(r['coin'], 0)) / (current_prices.get(r['coin']) or 1)) * 100, axis=1)

    col_left, col_right = st.columns([1.3, 0.7], gap="medium")

    with col_left:
        st.subheader(L["matrix_title"])
        for exp in sorted(df['expiry'].unique()):
            dt = datetime.fromtimestamp(exp // 1000).strftime("%m/%d %H:%M")
            st.write(f"📅 **{L['settlement']}: {dt}**")
            
            sub = df[df['expiry'] == exp].copy()
            
            # --- 排序逻辑：计算该行所有交易所中的最大收益率，并按此降序 ---
            # 首先创建透视表
            temp_pivot = sub.pivot_table(index=['coin', 'strike', dist_col], columns='platform', values='apy')
            
            # 补齐所有平台列
            for p in ['Binance', 'OKX', 'Bitget']:
                if p not in temp_pivot.columns: temp_pivot[p] = None
            
            # 计算每行的最大 APY 作为排序依据
            temp_pivot['max_apy'] = temp_pivot[['Binance', 'OKX', 'Bitget']].max(axis=1)
            temp_pivot = temp_pivot.sort_values('max_apy', ascending=False).drop(columns=['max_apy'])
            
            # 最终展示列排序
            final_df = temp_pivot[['Binance', 'OKX', 'Bitget']]
            
            st.dataframe(final_df.style.highlight_max(axis=1, color="#1e4620").format("{:.2f}%", na_rep="--"), 
                         width="stretch", key=f"df_{exp}_{st.session_state.lang}")

    with col_right:
        st.subheader(L["rank_title"])
        rank_df = df.sort_values("apy", ascending=False).head(30)
        st.dataframe(
            rank_df[['coin', 'platform', 'apy', 'strike', dist_col]]
            .style.background_gradient(subset=['apy'], cmap='YlGn')
            .format({dist_col: "{:.2f}%", "apy": "{:.2f}%"}),
            hide_index=True, width="stretch", height=1200, key=f"rank_{st.session_state.lang}"
        )