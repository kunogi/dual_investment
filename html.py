import streamlit as st
import pandas as pd
import requests
import time
import os
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables (e.g., DEFAULT_PROXY)
load_dotenv()

# --- 1. Internationalization (I18n) ---
LANG_DICT = {
    "zh": {
        "page_title": "Dual Investment Dashboard",
        "sidebar_ctrl": "🎮 Dashboard Control",
        "mode_toggle": "Switch to SELL HIGH Mode",
        "buy_low": "Buy Low",
        "sell_high": "Sell High",
        "current_strat": "Current Strategy",
        "asset_select": "Asset Selection:",
        "proxy_ctrl": "🌐 Proxy Control",
        "sync_btn": "⚡ Sync Data",
        "last_sync": "Last Sync",
        "matrix_title": "Alignment Matrix",
        "rank_title": "🏆 Global APY Ranking",
        "settlement": "Settlement",
        "asset_target": "Asset-Target",
        "target_price": "Target Price",
        "exchange": "Exchange",
        "no_data": "⚠️ No data found. Please check Proxy or Config."
    },
    "en": {
        "page_title": "Dual Investment Dashboard",
        "sidebar_ctrl": "🎮 Dashboard Control",
        "mode_toggle": "Switch to SELL HIGH mode",
        "buy_low": "Buy Low",
        "sell_high": "Sell High",
        "current_strat": "Strategy",
        "asset_select": "Asset Selection:",
        "proxy_ctrl": "🌐 Proxy Control",
        "sync_btn": "⚡ Sync Data",
        "last_sync": "Last Sync",
        "matrix_title": "Alignment Matrix",
        "rank_title": "🏆 Global APY Ranking",
        "settlement": "Settlement",
        "asset_target": "Asset-Target",
        "target_price": "Target Price",
        "exchange": "Exchange",
        "no_data": "⚠️ No data found. Check Proxy/Config."
    }
}

# --- 2. Page Configuration ---
st.set_page_config(page_title="Dual Investment Dashboard", layout="wide", page_icon="💰")

# Auto-detect browser locale (zh-CN -> zh, others -> en)
browser_locale = st.context.locale.split('-')[0] if st.context.locale else "en"
default_lang_idx = 0 if browser_locale == "zh" else 1

# --- 3. Asset Mapping Configuration ---
COIN_CONFIG = {
    "BTC":  {"okx_id": 0,     "binance_symbol": "BTC",  "bitget_id": 2},
    "ETH":  {"okx_id": 2,     "binance_symbol": "ETH",  "bitget_id": 3},
    "SOL":  {"okx_id": 880,   "binance_symbol": "SOL",  "bitget_id": 235},
    # "DOGE": {"okx_id": 1054,  "binance_symbol": "DOGE", "bitget_id": 82},
    "XAUT": {"okx_id": 16789, "binance_symbol": None,   "bitget_id": None}
}

# Proxy Settings from .env
env_proxy = os.getenv("DEFAULT_PROXY")
PROXY_SETTING = {"https": env_proxy, "http": env_proxy} if env_proxy else {}

# --- 4. Fetching Engines ---

def get_okx(cfg, name, use_proxy, mode):
    """
    OKX Fetching Engine:
    Uses 'PUT' for Buy Low and 'CALL' for Sell High.
    Note: OKX always expects the target asset ID in 'currencyId'.
    """
    if cfg.get("okx_id") is None: return []
    
    t = int(time.time() * 1000)
    # Fix: Both modes use Asset ID as primary, 7 (USDT) as alt
    curr_id = cfg['okx_id']
    alt_id = 7
    opt_type = "PUT" if mode == "Buy Low" else "CALL"
    
    url = f"https://www.okx.com/priapi/v2/sfp/dcd/products?currencyId={curr_id}&altCurrencyId={alt_id}&dcdOptionType={opt_type}&t={t}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.okx.com/",
        "Accept": "application/json",
    }
    proxies = PROXY_SETTING if (use_proxy and PROXY_SETTING) else {}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10, proxies=proxies)
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("data", {}).get("products", [])
            parsed = []
            for p in products:
                s, a, e = p.get("strike"), p.get("annualYieldPercentage"), p.get("expiryTime")
                if s and a and e:
                    parsed.append({
                        "coin": name, 
                        "strike": float(s), 
                        "apy": float(a), 
                        "expiry": int(e), 
                        "platform": "OKX"
                    })
            return parsed
    except:
        pass
    return []

def get_binance(cfg, name, use_proxy, mode):
    """Binance Fetching Engine: Differentiates by projectType (DOWN/UP)"""
    if cfg.get("binance_symbol") is None: return []
    proj_type = "DOWN" if mode == "Buy Low" else "UP"
    invest_asset = "USDT" if mode == "Buy Low" else cfg["binance_symbol"]
    target_asset = cfg["binance_symbol"] if mode == "Buy Low" else "USDT"
    
    url = "https://www.binance.com/bapi/earn/v5/friendly/pos/dc/project/list"
    params = {
        "investmentAsset": invest_asset, 
        "targetAsset": target_asset, 
        "projectType": proj_type, 
        "sortType": "APY_DESC", 
        "pageSize": 100
    }
    proxies = PROXY_SETTING if (use_proxy and PROXY_SETTING) else {}
    try:
        resp = requests.get(url, params=params, timeout=10, proxies=proxies)
        data = resp.json()
        parsed = []
        for i in data.get("data", {}).get("list", []):
            parsed.append({
                "coin": name, 
                "strike": float(i["strikePrice"]), 
                "apy": float(i["apr"]) * 100, 
                "expiry": int(i["settleTime"]), 
                "platform": "Binance"
            })
        return parsed
    except: 
        return []

def get_bitget(cfg, name, use_proxy, mode):
    """Bitget Fetching Engine: Differentiates by direction (0=BuyLow, 1=SellHigh)"""
    if cfg.get("bitget_id") is None: return []
    direction = 0 if mode == "Buy Low" else 1
    url = "https://www.bitget.cloud/v1/finance/dualInvest/ordinary/product/list"
    payload = {"productTokenId": cfg["bitget_id"], "tradeTokenId": 2, "direction": direction}
    proxies = PROXY_SETTING if (use_proxy and PROXY_SETTING) else {}
    try:
        resp = requests.post(url, json=payload, timeout=10, proxies=proxies)
        data = resp.json()
        parsed = []
        if data.get("code") == "200":
            for group in data["data"]:
                for item in group.get("productList", []):
                    parsed.append({
                        "coin": name, 
                        "strike": float(item["targetPrice"]), 
                        "apy": float(item["apy"]), 
                        "expiry": int(group["settleDate"]), 
                        "platform": "Bitget"
                    })
        return parsed
    except: 
        return []

# --- 5. User Interface (Sidebar) ---

with st.sidebar:
    lang_ui = st.selectbox("🌐 Language / 语言", ["English", "中文"], index=default_lang_idx)
    L = LANG_DICT["en"] if lang_ui == "English" else LANG_DICT["zh"]
    
    st.header(L["sidebar_ctrl"])
    # Dual Mode Switcher
    invest_mode = st.toggle(L["mode_toggle"], value=False)
    current_mode_key = "Sell High" if invest_mode else "Buy Low"
    st.info(f"{L['current_strat']}: **{L['sell_high'] if invest_mode else L['buy_low']}**")
    
    st.write("---")
    # Menu Selection
    menu_options = ["Hybrid Dashboard"] + list(COIN_CONFIG.keys())
    target = st.radio(L["asset_select"], menu_options, index=0)
    
    st.write("---")
    st.subheader(L["proxy_ctrl"])
    proxy_okx = st.checkbox("OKX Proxy", value=True)
    proxy_binance = st.checkbox("Binance Proxy", value=True)
    proxy_bitget = st.checkbox("Bitget Proxy", value=True)
    
    refresh_clicked = st.button(f"{L['sync_btn']} ({target})", type="primary", use_container_width=True)

# --- 6. Main Content Rendering ---

st.title(L["page_title"])

def render_dashboard(data_list, title, mode_key):
    if not data_list:
        st.warning(L["no_data"])
        return

    is_mixed = title == "Hybrid Dashboard"
    col_l, col_r = st.columns([1.2, 0.8], gap="large")

    with col_l:
        st.subheader(f"📅 {title} ({L['sell_high'] if mode_key == 'Sell High' else L['buy_low']})")
        grouped = defaultdict(lambda: defaultdict(dict))
        
        # Matrix grouping by Expiry and Rounded Strike Price
        for item in data_list:
            if item["coin"] in ["BTC", "ETH", "XAUT"]: step = 25
            elif item["coin"] == "SOL": step = 5
            elif item["strike"] < 1: step = 0.01
            else: step = 1
            
            strike_rounded = round(item["strike"] / step) * step if step != 0 else item["strike"]
            row_key = f"{item['coin']}-{strike_rounded}" if is_mixed else strike_rounded
            grouped[item["expiry"]][row_key][item["platform"]] = item["apy"]

        for expiry in sorted(grouped.keys()):
            dt_str = datetime.fromtimestamp(expiry // 1000).strftime("%m/%d %H:%M")
            st.markdown(f"**📍 {L['settlement']}: {dt_str}**")
            label = L["asset_target"] if is_mixed else L["target_price"]
            
            df_l = pd.DataFrame([
                {label: k, "OKX(%)": a.get("OKX"), "Binance(%)": a.get("Binance"), "Bitget(%)": a.get("Bitget")} 
                for k, a in grouped[expiry].items()
            ])
            
            # Sort by highest APY available for that strike price
            num_cols = ["OKX(%)", "Binance(%)", "Bitget(%)"]
            df_l["_sort"] = df_l[num_cols].max(axis=1)
            df_l = df_l.sort_values("_sort", ascending=False).drop(columns=["_sort"])
            
            st.dataframe(
                df_l.style.highlight_max(axis=1, subset=num_cols, color="#1e4620")
                .format("{:.2f}", subset=num_cols, na_rep="--"), 
                width="stretch", hide_index=True
            )

    with col_r:
        st.subheader(L["rank_title"])
        rank_df = pd.DataFrame(data_list)
        rank_df[L["settlement"]] = rank_df["expiry"].apply(
            lambda x: datetime.fromtimestamp(x // 1000).strftime("%m/%d %H:%M")
        )
        
        # Determine columns based on display mode
        cols = ["coin", "platform", "apy", "strike", L["settlement"]] if is_mixed else ["platform", "apy", "strike", L["settlement"]]
        rank_df = rank_df[cols].sort_values("apy", ascending=False).rename(
            columns={"coin": "Asset", "platform": L["exchange"], "apy": "APY(%)", "strike": L["target_price"]}
        )
        
        st.dataframe(
            rank_df.style.background_gradient(subset=["APY(%)"], cmap="YlGn")
            .format({"APY(%)": "{:.2f}"}), 
            width="stretch", hide_index=True, height=800
        )

# Data fetching execution
main_container = st.empty()
with main_container.container():
    all_data = []
    with st.spinner(f"Fetching {current_mode_key} data..."):
        targets = COIN_CONFIG.items() if target == "Hybrid Dashboard" else [(target, COIN_CONFIG[target])]
        for name, cfg in targets:
            all_data += get_okx(cfg, name, proxy_okx, current_mode_key)
            all_data += get_binance(cfg, name, proxy_binance, current_mode_key)
            all_data += get_bitget(cfg, name, proxy_bitget, current_mode_key)
    
    render_dashboard(all_data, target, current_mode_key)