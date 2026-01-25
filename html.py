import streamlit as st
import pandas as pd
import requests
import time
import os
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

# Load configuration from .env file
load_dotenv()

# 1. Page Configuration
st.set_page_config(page_title="Dual Investment Hunter", layout="wide", page_icon="💰")

# 2. Core Configuration (Add new assets here, use None if not supported by exchange)
COIN_CONFIG = {
    "BTC":  {"okx_id": 0,     "binance_symbol": "BTC",  "bitget_id": 2},
    "ETH":  {"okx_id": 2,     "binance_symbol": "ETH",  "bitget_id": 3},
    "SOL":  {"okx_id": 880,   "binance_symbol": "SOL",  "bitget_id": 235},
    # "DOGE": {"okx_id": 1054,  "binance_symbol": "DOGE", "bitget_id": 82},
    "XAUT": {"okx_id": 16789, "binance_symbol": None,   "bitget_id": None}
}

# Load Proxy from Environment Variables
env_proxy = os.getenv("DEFAULT_PROXY")
PROXY_SETTING = {"https": env_proxy, "http": env_proxy} if env_proxy else {}

# Initialize Persistent HTTP Session
if "http_session" not in st.session_state:
    st.session_state.http_session = requests.Session()

# --- Fetching Engine (Dynamic Proxy & None-Safety) ---

def fast_request(url, method="GET", params=None, json_data=None, use_proxy=False):
    headers = {"User-Agent": "Mozilla/5.0"}
    proxies = PROXY_SETTING if (use_proxy and PROXY_SETTING) else {}
    try:
        if method == "GET":
            resp = st.session_state.http_session.get(url, params=params, headers=headers, timeout=5, proxies=proxies)
        else:
            resp = st.session_state.http_session.post(url, json=json_data, headers=headers, timeout=5, proxies=proxies)
        return resp.json()
    except:
        return None

def get_okx(cfg, name, use_proxy):
    if cfg.get("okx_id") is None: return []
    t = int(time.time() * 1000)
    url = f"https://www.okx.com/priapi/v2/sfp/dcd/products?currencyId={cfg['okx_id']}&altCurrencyId=7&dcdOptionType=PUT&t={t}"
    res = fast_request(url, use_proxy=use_proxy)
    parsed = []
    if res and res.get("data"):
        for p in res.get("data", {}).get("products", []):
            try:
                s, a = p.get("strike"), p.get("annualYieldPercentage")
                if s and a and str(s).strip() != "" and str(a).strip() != "":
                    parsed.append({"coin": name, "strike": float(s), "apy": float(a), "expiry": p["expiryTime"], "platform": "OKX"})
            except: continue
    return parsed

def get_binance(cfg, name, use_proxy):
    if cfg.get("binance_symbol") is None: return []
    url = "https://www.binance.com/bapi/earn/v5/friendly/pos/dc/project/list"
    params = {"investmentAsset": "USDT", "targetAsset": cfg["binance_symbol"], "projectType": "DOWN", "sortType": "APY_DESC", "pageSize": 100}
    res = fast_request(url, params=params, use_proxy=use_proxy)
    parsed = []
    if res and res.get("data"):
        for i in res.get("data", {}).get("list", []):
            try:
                parsed.append({"coin": name, "strike": float(i["strikePrice"]), "apy": float(i["apr"]) * 100, "expiry": int(i["settleTime"]), "platform": "Binance"})
            except: continue
    return parsed

def get_bitget(cfg, name, use_proxy):
    if cfg.get("bitget_id") is None: return []
    url = "https://www.bitget.cloud/v1/finance/dualInvest/ordinary/product/list"
    payload = {"productTokenId": cfg["bitget_id"], "tradeTokenId": 2, "direction": 0}
    res = fast_request(url, method="POST", json_data=payload, use_proxy=use_proxy)
    parsed = []
    if res and res.get("code") == "200" and res.get("data"):
        for group in res["data"]:
            for item in group.get("productList", []):
                try:
                    parsed.append({"coin": name, "strike": float(item["targetPrice"]), "apy": float(item["apy"]), "expiry": int(group["settleDate"]), "platform": "Bitget"})
                except: continue
    return parsed

# --- UI Rendering Function ---

def render_dashboard(data_list, title):
    if not data_list:
        st.warning(f"⚠️ No data found for {title}. Check Proxy or config.")
        return

    is_mixed = title == "Hybrid Dashboard"
    col_l, col_r = st.columns([1.2, 0.8], gap="large")

    with col_l:
        st.subheader(f"📅 {title}: Alignment Matrix")
        grouped = defaultdict(lambda: defaultdict(dict))
        for item in data_list:
            # Intelligent step selection
            if item["coin"] in ["BTC", "ETH", "XAUT"]:
                step = 25
            elif item["coin"] == "SOL":
                step = 5
            else:
                # Automatic step for small assets like DOGE
                step = 0.01 if item["strike"] < 1 else 1
            
            strike_rounded = round(item["strike"] / step) * step if step != 0 else item["strike"]
            row_key = f"{item['coin']}-{strike_rounded}" if is_mixed else strike_rounded
            grouped[item["expiry"]][row_key][item["platform"]] = item["apy"]

        for expiry in sorted(grouped.keys()):
            dt_str = datetime.fromtimestamp(expiry // 1000).strftime("%m/%d %H:%M")
            st.markdown(f"**📍 Settlement: {dt_str}**")
            label = "Asset-Target" if is_mixed else "Target Price"
            
            df_l = pd.DataFrame([{label: k, "OKX(%)": a.get("OKX"), "Binance(%)": a.get("Binance"), "Bitget(%)": a.get("Bitget")} 
                                 for k, a in grouped[expiry].items()])
            
            # Smart Sorting: Show highest yield opportunities on top
            num_cols = ["OKX(%)", "Binance(%)", "Bitget(%)"]
            df_l["_best_apy"] = df_l[num_cols].max(axis=1)
            df_l = df_l.sort_values("_best_apy", ascending=False).drop(columns=["_best_apy"])

            st.dataframe(df_l.style.highlight_max(axis=1, subset=num_cols, color="#1e4620")
                         .format("{:.2f}", subset=num_cols, na_rep="--"), width="stretch", hide_index=True)

    with col_r:
        st.subheader("🏆 Global APY Ranking")
        rank_df = pd.DataFrame(data_list)
        rank_df["Settlement Time"] = rank_df["expiry"].apply(lambda x: datetime.fromtimestamp(x // 1000).strftime("%m/%d %H:%M"))
        cols = ["coin", "platform", "apy", "strike", "Settlement Time"] if is_mixed else ["platform", "apy", "strike", "Settlement Time"]
        rank_df = rank_df[cols].sort_values("apy", ascending=False).rename(columns={"coin": "Asset", "platform": "Exchange", "apy": "APY(%)", "strike": "Target"})
        
        try:
            styled_df = rank_df.style.background_gradient(subset=["APY(%)"], cmap="YlGn").format({"APY(%)": "{:.2f}"})
        except:
            styled_df = rank_df.style.format({"APY(%)": "{:.2f}"})
        st.dataframe(styled_df, width="stretch", hide_index=True, height=800)

# --- Main Application Flow ---

st.title("🚀 Dual Investment Hunter")

with st.sidebar:
    st.header("⚙️ Settings")
    # Dynamic menu generation from COIN_CONFIG
    menu_options = ["Hybrid Dashboard"] + list(COIN_CONFIG.keys())
    target = st.radio("View Mode:", menu_options, index=0)
    
    st.write("---")
    st.subheader("🌐 Proxy Control")
    if env_proxy:
        st.success(f"System Proxy: {env_proxy}")
    else:
        st.warning("No .env proxy found. Direct mode active.")
        
    proxy_okx = st.checkbox("OKX Proxy", value=True)
    proxy_binance = st.checkbox("Binance Proxy", value=True)
    proxy_bitget = st.checkbox("Bitget Proxy", value=True)
    
    st.write("---")
    refresh_clicked = st.button(f"⚡ Refresh {target}", type="primary", use_container_width=True)
    st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")

main_container = st.empty()

with main_container.container():
    all_data = []
    with st.spinner(f"Scanning {target} markets..."):
        if target == "Hybrid Dashboard":
            for name, cfg in COIN_CONFIG.items():
                all_data += get_okx(cfg, name, proxy_okx)
                all_data += get_binance(cfg, name, proxy_binance)
                all_data += get_bitget(cfg, name, proxy_bitget)
        else:
            cfg = COIN_CONFIG[target]
            all_data = (get_okx(cfg, target, proxy_okx) + 
                        get_binance(cfg, target, proxy_binance) + 
                        get_bitget(cfg, target, proxy_bitget))
    
    render_dashboard(all_data, target)
    if refresh_clicked:
        st.toast(f"{target} synchronization complete!")