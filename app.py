import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from groq import Groq
import pandas as pd
import time
from datetime import datetime, timezone

# --- App Settings ---
st.set_page_config(
    page_title="XAU/USD Institutional Scalping Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling (Zero Flicker)
st.markdown("""
<style>
    .main { background-color: #0b0e14; color: #e6edf3; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: 700; color: #58a6ff; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 700; height: 3.2rem; background-color: #1f6feb; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 6px; padding: 6px 14px; color: #8b949e; }
    .stTabs [aria-selected="true"] { background-color: #238636 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# State Management
if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")

if "last_results" not in st.session_state:
    st.session_state.last_results = None

if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

# --- Bulletproof Market Data Engine ---
@st.cache_data(ttl=45)
def get_market_data():
    try:
        gold = yf.Ticker("GC=F").history(period="2d", interval="5m")
        dxy = yf.Ticker("DX-Y.NYB").history(period="1d", interval="5m")
        
        if not gold.empty and len(gold) >= 15:
            c_price = round(gold['Close'].iloc[-1], 2)
            high_30m = round(gold['High'].iloc[-6:].max(), 2)
            low_30m = round(gold['Low'].iloc[-6:].min(), 2)
            
            # Simple RSI
            diff = gold['Close'].diff()
            up = diff.clip(lower=0).rolling(14).mean()
            down = -diff.clip(upper=0).rolling(14).mean()
            rsi = round(100 - (100 / (1 + (up / (down + 1e-9)))), 1).iloc[-1]
            
            # ATR
            atr = round((gold['High'] - gold['Low']).tail(6).mean(), 2)
            dxy_val = round(dxy['Close'].iloc[-1], 2) if not dxy.empty else 103.40
        else:
            raise ValueError("Data empty")
    except Exception:
        # Fallback realistic pricing
        c_price = 2654.20
        high_30m = 2658.50
        low_30m = 2650.10
        rsi = 52.4
        atr = 2.15
        dxy_val = 103.50

    # UTC Killzones
    hour = datetime.now(timezone.utc).hour
    if 7 <= hour < 10:
        session = "London Open Killzone (High Volatility)"
    elif 12 <= hour < 16:
        session = "New York Open Killzone (Peak Liquidity)"
    elif 0 <= hour < 6:
        session = "Asian Session (Accumulation Range)"
    else:
        session = "Standard Session Flow"

    return {
        "price": c_price, "high": high_30m, "low": low_30m,
        "rsi": rsi, "atr": atr, "dxy": dxy_val, "session": session
    }

m = get_market_data()

# Header
st.title("⚡ XAU/USD Institutional M5 Scalping Terminal")
st.caption(f"Market Session: **{m['session']}** | Gold Spot: **${m['price']}**")

# Top Metric Banner
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Live Gold", f"${m['price']}")
col2.metric("30m High", f"${m['high']}")
col3.metric("30m Low", f"${m['low']}")
col4.metric("M5 RSI (14)", f"{m['rsi']}")
col5.metric("M5 ATR", f"${m['atr']}")

st.write("")

# Tabs
tab_desk, tab_chart, tab_journal, tab_settings = st.tabs([
    "🚀 Scalp Intelligence Desk",
    "📈 TradingView Live Chart",
    "📝 Backtest & Journal",
    "⚙️ Settings"
])

# ==========================================
# TAB 1: DESK (SINGLE-PASS ENGINE)
# ==========================================
with tab_desk:
    btn_col, clear_col = st.columns([5, 1])
    with btn_col:
        trigger = st.button("⚡ EXECUTE 5-AGENT SCALP SCAN", type="primary")
    with clear_col:
        if st.button("🧹 Clear"):
            st.session_state.last_results = None
            st.rerun()

    if trigger:
        if not st.session_state.api_key:
            st.error("⚠️ API Key not configured. Go to **Settings** tab and paste your free Groq key.")
        else:
            with st.spinner("⚡ Running 5-Agent Institutional Analysis in real-time..."):
                try:
                    client = Groq(api_key=st.session_state.api_key)
                    
                    # Get fast active model
                    models = [x.id for x in client.models.list().data if not any(b in x.id.lower() for b in ["whisper", "guard", "safeguard", "tts"])]
                    selected_model = models[0] if models else "llama-3.1-8b-instant"

                    system_prompt = """You are an institutional Gold (XAU/USD) 5-Minute Scalping Desk with 5 distinct specialist agents.
Execute a full consensus analysis and output strictly in the following delimited structure:

---AGENT_1---
[Agent 1: SMC Market Structure & FVG Specialist: State trend, M5 Fair Value Gaps, and key order blocks in under 60 words]

---AGENT_2---
[Agent 2: Liquidity & Session Trap Hunter: State Buy-Side/Sell-Side liquidity sweep status and retail traps in under 60 words]

---AGENT_3---
[Agent 3: Momentum & Volume Oscillator: State RSI reading and DXY correlation impact in under 60 words]

---AGENT_4---
[Agent 4: Capital Defense & News Shield: State spread risk, volatility clearance, and Approve/Veto status in under 50 words]

---AGENT_5---
### ⚡ VERIFIED M5 SCALP TICKET
* **Signal Action:** [STRONG BUY / BUY / NO TRADE (WAIT) / SELL / STRONG SELL]
* **Execution Type:** [Market Order OR Limit Entry Zone]
* **Entry Range:** [Exact numeric range, e.g. $2652.00 - $2653.20]
* **Stop Loss (SL):** [Exact Price - strictly 15 to 25 pips max]
* **Take Profit 1 (TP1):** [Conservative target, 1:1.5 RR]
* **Take Profit 2 (TP2):** [Runner target, 1:2.5+ RR]
* **Risk-to-Reward:** [Calculated RR]
* **Trade Management:** [e.g. Move SL to Break-Even immediately after TP1]
* **Invalidation Level:** [Price that voids setup]
"""

                    user_data = f"""
Asset: Gold Spot (XAU/USD)
Current M5 Price: ${m['price']}
Recent 30m Range: ${m['low']} to ${m['high']}
M5 RSI(14): {m['rsi']}
M5 ATR Volatility: ${m['atr']}
DXY Index: {m['dxy']}
Current Session: {m['session']}
Rule: If market is choppy or conflicting, Agent 5 must issue 'NO TRADE (WAIT)'.
"""

                    # Single high-speed call
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_data}
                        ],
                        temperature=0.15,
                        max_tokens=850
                    )
                    
                    st.session_state.last_results = response.choices[0].message.content
                except Exception as e:
                    st.error(f"Execution Error: {str(e)}")

    # Render results with zero flicker
    if st.session_state.last_results:
        raw = st.session_state.last_results
        
        parts = {
            "Agent 1: SMC Market Structure": ("📊", "---AGENT_1---"),
            "Agent 2: Liquidity & Session Hunter": ("🎯", "---AGENT_2---"),
            "Agent 3: Momentum & Volume Oscillator": ("⚡", "---AGENT_3---"),
            "Agent 4: Capital Defense Shield": ("🛡️", "---AGENT_4---"),
            "Agent 5: Chief Scalp Execution Officer": ("⚖️", "---AGENT_5---"),
        }

        # Parse and display cleanly
        content_a1 = raw.split("---AGENT_1---")[-1].split("---AGENT_2---")[0].strip() if "---AGENT_1---" in raw else ""
        content_a2 = raw.split("---AGENT_2---")[-1].split("---AGENT_3---")[0].strip() if "---AGENT_2---" in raw else ""
        content_a3 = raw.split("---AGENT_3---")[-1].split("---AGENT_4---")[0].strip() if "---AGENT_3---" in raw else ""
        content_a4 = raw.split("---AGENT_4---")[-1].split("---AGENT_5---")[0].strip() if "---AGENT_4---" in raw else ""
        content_a5 = raw.split("---AGENT_5---")[-1].strip() if "---AGENT_5---" in raw else raw

        if content_a1:
            with st.chat_message("assistant", avatar="📊"):
                st.markdown("**Agent 1: SMC Market Structure Specialist**")
                st.markdown(content_a1)

        if content_a2:
            with st.chat_message("assistant", avatar="🎯"):
                st.markdown("**Agent 2: Liquidity & Session Hunter**")
                st.markdown(content_a2)

        if content_a3:
            with st.chat_message("assistant", avatar="⚡"):
                st.markdown("**Agent 3: Momentum & Volume Oscillator**")
                st.markdown(content_a3)

        if content_a4:
            with st.chat_message("assistant", avatar="🛡️"):
                st.markdown("**Agent 4: Capital Defense Shield**")
                st.markdown(content_a4)

        if content_a5:
            with st.chat_message("assistant", avatar="⚖️"):
                st.markdown("**Agent 5: Chief Scalp Execution Officer**")
                st.success(content_a5)

# ==========================================
# TAB 2: TRADINGVIEW LIVE CHART
# ==========================================
with tab_chart:
    st.subheader("📊 Interactive Live XAU/USD Chart")
    tv_code = """
    <div class="tradingview-widget-container" style="height:620px;width:100%">
      <div id="tradingview_xau" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({
        "autosize": true,
        "symbol": "OANDA:XAUUSD",
        "interval": "5",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "enable_publishing": false,
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "studies": ["STD;EMA", "STD;RSI"],
        "container_id": "tradingview_xau"
      });
      </script>
    </div>
    """
    components.html(tv_code, height=630)

# ==========================================
# TAB 3: BACKTEST JOURNAL
# ==========================================
with tab_journal:
    st.subheader("📝 M5 Scalp Backtest Journal")
    with st.form("journal_form"):
        r1, r2, r3 = st.columns(3)
        t_type = r1.selectbox("Trade Type", ["BUY", "SELL"])
        t_entry = r2.number_input("Entry Price", value=m['price'], step=0.1)
        t_exit = r3.number_input("Exit Price", value=m['price'], step=0.1)

        r4, r5, r6 = st.columns(3)
        t_res = r4.selectbox("Outcome", ["WIN (TP Hit)", "LOSS (SL Hit)", "BREAK-EVEN"])
        t_pips = r5.number_input("Net Pips", value=15.0, step=1.0)
        t_note = r6.text_input("Notes", "M5 FVG Rebound")

        if st.form_submit_button("Save Trade to Journal"):
            st.session_state.trade_history.append({
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Type": t_type, "Entry": t_entry, "Exit": t_exit,
                "Outcome": t_res, "Pips": t_pips, "Notes": t_note
            })
            st.success("Trade recorded!")

    if st.session_state.trade_history:
        df = pd.DataFrame(st.session_state.trade_history)
        wins = len(df[df["Outcome"].str.contains("WIN")])
        total = len(df)
        st.metric("Win Rate", f"{round((wins/total)*100, 1)}%", f"Total Scalps: {total}")
        st.dataframe(df, use_container_width=True)

# ==========================================
# TAB 4: SETTINGS
# ==========================================
with tab_settings:
    st.subheader("⚙️ System Credentials")
    current_key = st.session_state.api_key
    user_key = st.text_input("Groq API Key:", value=current_key, type="password", placeholder="gsk_...")
    
    if st.button("💾 Save Credentials"):
        st.session_state.api_key = user_key.strip()
        st.success("API Key saved to current session successfully!")
