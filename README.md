
# 🚀 Dual Investment Dashboard

**Dual Investment Dashboard** is a high-performance, real-time aggregator designed for cryptocurrency traders. It monitors and compares **Dual Investment (Dual Currency)** yield opportunities for **BTC, ETH, and SOL** across three major exchanges: **Binance, OKX, and Bitget**.

By aligning products by settlement date and target price, it helps you find the highest APY in seconds.

### ✨ Key Features
- **Real-time Aggregation**: Sub-second data fetching from Binance, OKX, and Bitget APIs.

- **Hybrid Dashboard**: A unified view to compare yields across all supported assets with explicit coin-price labels.

- **Alignment Matrix**: Automatically groups products by settlement time for easy horizontal comparison.

- **Dynamic Proxy Control**: Fine-grained proxy settings for each exchange via the UI.

---

# 🚀 双币投资看板

看板通过实时监控并对比 Binance、OKX 和 Bitget 三大交易所关于 BTC、ETH 和 SOL 的 **双币投资（理财）** 收益机会。

通过按结算日期和目标价对齐产品，它可以帮助你在几秒钟内找到全网最高年化收益（APY）的产品。

### ✨ 核心功能
- **实时聚合**：从 Binance、OKX 和 Bitget API 进行秒级数据抓取。

- **混合大榜**：提供统一视图，横向对比所有支持币种的收益，并带有清晰的“币种-价格”标识。

- **对齐看板**：自动按结算时间分组，方便进行平台间的横向比价。

- **精细化代理控制**：支持在 UI 界面为每家交易所单独开关代理。

---

# 🛠️ 安装配置与使用 Installation & Setup

**Clone the repository:**
   ```bash
   git clone https://github.com/kunogi/dual_investment.git
   cd dual_investment
```

**Create a virtual environment (optional):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Configure Proxy: Create a .env file in the root directory:**
```bash
DEFAULT_PROXY=http://127.0.0.1:7897 or None
```

**Run the application:**
```bash
streamlit run html.py
```