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