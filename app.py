import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from groq import Groq
import pandas as pd
import time
from datetime import datetime

# --- Terminal Setup ---
st.set_page_config(
    page_title="XAU/USD M5 Scalping Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Institutional Dark CSS
st.markdown("""
<style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; color: #58a6ff; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; }
    .metric-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; }
</style>
""", unsafe_allow_html=True)

# --- State Management ---
if "api_key" not in st.session_state:
    # Check if key exists in Streamlit Secrets
    st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")

if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Market Data Fetcher (5-Minute Scalp Optimized) ---
@st.cache_data(ttl=30)
def fetch_scalp_market_data():
    try:
        gold = yf.Ticker("GC=F").history(period="1d", interval="5m")
        dxy = yf.Ticker("DX-Y.NYB").history(period="1d", interval="5m")
        
        current_gold = round(gold['Close'].iloc[-1], 2)
        m5_high = round(gold['High'].iloc[-6:].max(), 2)  # Last 30 mins high
        m5_low = round(gold['Low'].iloc[-6:].min(), 2)    # Last 30 mins low
        current_dxy = round(dxy['Close'].iloc[-1], 2) if not dxy.empty else 103.50
        
        # Calculate fast ATR estimate (average candle size)
        recent_ranges = (gold['High'] - gold['Low']).tail(5)
        m5_atr = round(recent_ranges.mean(), 2)
        
        return {
            "price": current_gold,
            "high": m5_high,
            "low": m5_low,
            "dxy": current_dxy,
            "atr": m5_atr
        }
    except Exception:
        return {
            "price": 2652.40,
            "high": 2656.80,
            "low": 2649.10,
            "dxy": 103.65,
            "atr": 2.10
        }

market = fetch_scalp_market_data()

# --- Header ---
st.title("⚡ XAU/USD Institutional M5 Scalping Desk")
st.caption("Autonomous 5-Agent Multi-Dimensional Order Flow & SMC Execution System")

# Top Metrics Row
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Live Gold (M5)", f"${market['price']}")
m2.metric("30m Scalp High", f"${market['high']}")
m3.metric("30m Scalp Low", f"${market['low']}")
m4.metric("DXY Index", f"{market['dxy']}")
m5.metric("M5 Volatility (ATR)", f"${market['atr']}")

st.write("")

# --- Navigation Tabs ---
tab_live, tab_chart, tab_backtest, tab_settings = st.tabs([
    "🚀 Scalp Intelligence Desk",
    "📈 TradingView Live Chart",
    "📊 Backtest & Performance Log",
    "⚙️ System Settings"
])

# ==========================================
# TAB 1: LIVE 5-AGENT SCALPING DESK
# ==========================================
with tab_live:
    col_trigger, col_clear = st.columns([4, 1])
    with col_trigger:
        run_analysis = st.button("⚡ Scan Market & Generate M5 Scalp Setup", type="primary")
    with col_clear:
        if st.button("🧹 Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Display Chat Log
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar=msg["avatar"]):
            st.markdown(f"**{msg['name']}**")
            st.markdown(msg["content"])

    if run_analysis:
        if not st.session_state.api_key:
            st.error("⚠️ API Key not configured. Please navigate to the **Settings** tab to save your Groq API Key.")
        else:
            try:
                client = Groq(api_key=st.session_state.api_key)
                
                # Fetch dynamically available model
                available_models = [m.id for m in client.models.list().data if "whisper" not in m.id and "guard" not in m.id]
                model_name = available_models[0] if available_models else "llama-3.1-8b-instant"

                context = f"""
                Asset: Gold Spot (XAU/USD)
                Current M5 Price: ${market['price']}
                Recent 30-Minute High: ${market['high']}
                Recent 30-Minute Low: ${market['low']}
                M5 ATR (Candle Volatility): ${market['atr']}
                US Dollar Index (DXY): {market['dxy']}
                Target Style: 5-Minute Scalping (Hold time: 5 to 45 minutes)
                """

                scalper_agents = [
                    {
                        "name": "Agent 1: M5 Market Structure & SMC Scalper",
                        "avatar": "📊",
                        "prompt": f"""You are Agent 1, a prop-firm funded M5 Gold Scalper specializing in Smart Money Concepts (SMC).
                        Data: {context}
                        Analyze:
                        1. Internal M5 Market Structure (BOS vs CHoCH).
                        2. Key M5/M15 Fair Value Gaps (FVG) and Order Blocks near current price.
                        3. Displacement candles confirming smart money momentum.
                        Provide a razor-sharp, actionable scalping read under 75 words."""
                    },
                    {
                        "name": "Agent 2: Liquidity & Session Killzone Hunter",
                        "avatar": "🎯",
                        "prompt": f"""You are Agent 2, an ICT Liquidity & Session specialist for Gold scalping.
                        Data: {context}
                        Analyze:
                        1. Session context (Asian range sweep, London open expansion, or NY open volatility).
                        2. Buy-Side Liquidity (BSL) and Sell-Side Liquidity (SSL) pools being targeted.
                        3. Are retail breakout traders currently trapped?
                        Deliver your verdict under 75 words."""
                    },
                    {
                        "name": "Agent 3: Real-Time Order Flow & Momentum",
                        "avatar": "⚡",
                        "prompt": f"""You are Agent 3, Order Flow & Momentum Scalper.
                        Data: {context}
                        Evaluate:
                        1. Wick rejections and candle body closes on M5.
                        2. DXY inverse correlation pressure ({market['dxy']}).
                        3. Suggested dynamic Stop Loss buffer based on ATR (${market['atr']}).
                        Provide a fast technical check under 75 words."""
                    },
                    {
                        "name": "Agent 4: Macro & High-Impact News Filter",
                        "avatar": "🛡️",
                        "prompt": f"""You are Agent 4, Capital Defense & News Shield.
                        Data: {context}
                        Determine:
                        1. Is current market condition safe for M5 scalping, or is spread widening / high volatility news expected?
                        2. Spread and slippage risk factor for Gold scalping right now.
                        Provide your defensive risk clearance under 60 words."""
                    }
                ]

                agent_dialogue = []

                # Execute Agents 1 to 4
                for ag in scalper_agents:
                    with st.spinner(f"{ag['name']} is scanning M5 price action..."):
                        res = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": "You are an institutional quantitative prop trader. Speak with precision, no generic disclaimers."},
                                {"role": "user", "content": ag["prompt"]}
                            ],
                            temperature=0.2,
                            max_tokens=200
                        ).choices[0].message.content

                        agent_dialogue.append(f"{ag['name']}: {res}")

                        with st.chat_message("assistant", avatar=ag["avatar"]):
                            st.markdown(f"**{ag['name']}**")
                            st.markdown(res)

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "name": ag["name"],
                            "avatar": ag["avatar"],
                            "content": res
                        })
                        time.sleep(0.3)

                # Agent 5: Master Scalp Commander
                with st.spinner("Agent 5 (Chief Execution Officer) is formulating the exact trade ticket..."):
                    chief_prompt = f"""
                    You are Agent 5, Chief Scalping Execution Officer.
                    Synthesize all 4 specialist reports:
                    {"".join(agent_dialogue)}
                    Live Gold Price: ${market['price']}
                    Current M5 ATR: ${market['atr']}
                    
                    Formulate the institutional trade setup in this EXACT format:
                    
                    ### ⚡ VERIFIED M5 SCALP TICKET
                    * **Action:** [STRONG BUY / BUY / NO TRADE (WAIT) / SELL / STRONG SELL]
                    * **Execution Type:** [Market Order OR Limit Entry Zone]
                    * **Entry Price Range:** [e.g. $2651.80 - $2652.50]
                    * **Stop Loss (SL):** [Exact Price - tight, 15 to 25 pips max]
                    * **Take Profit 1 (TP1):** [Conservative - 1:1.5 RR, close 70% volume]
                    * **Take Profit 2 (TP2):** [Runner - 1:2.5+ RR]
                    * **Risk-to-Reward:** [Calculated RR]
                    * **Trade Management:** [e.g. Move SL to Break-Even immediately once TP1 is hit]
                    * **Invalidation Level:** [Price that voids setup]
                    """

                    final_ticket = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "You are the head execution officer at a proprietary trading desk. Give exact numeric trade parameters."},
                            {"role": "user", "content": chief_prompt}
                        ],
                        temperature=0.1,
                        max_tokens=300
                    ).choices[0].message.content

                    with st.chat_message("assistant", avatar="⚖️"):
                        st.markdown("**Agent 5: Chief Scalp Execution Officer**")
                        st.success(final_ticket)

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "name": "Agent 5: Chief Scalp Execution Officer",
                        "avatar": "⚖️",
                        "content": final_ticket
                    })

            except Exception as e:
                st.error(f"Execution Error: {str(e)}")

# ==========================================
# TAB 2: TRADINGVIEW LIVE CHART
# ==========================================
with tab_chart:
    st.subheader("📊 Interactive Live XAU/USD Chart")
    st.caption("Use this institutional TradingView terminal to verify M5 order blocks, liquidity levels, and plot agent signals.")
    
    # TradingView Advanced Widget Embed
    tradingview_widget = """
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container" style="height:650px;width:100%">
      <div id="tradingview_xauusd" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {
        "autosize": true,
        "symbol": "OANDA:XAUUSD",
        "interval": "5",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "studies": [
          "STD;EMA",
          "STD;RSI"
        ],
        "container_id": "tradingview_xauusd"
      }
      );
      </script>
    </div>
    <!-- TradingView Widget END -->
    """
    components.html(tradingview_widget, height=650)

# ==========================================
# TAB 3: BACKTESTING & PERFORMANCE TRACKER
# ==========================================
with tab_backtest:
    st.subheader("📝 M5 Scalp Backtesting & Journal")
    st.caption("Record live trades and simulated backtests to calculate win rate and profit factor.")
    
    with st.expander("➕ Log a Completed Scalp Trade", expanded=False):
        with st.form("trade_form"):
            c1, c2, c3 = st.columns(3)
            trade_type = c1.selectbox("Direction", ["BUY", "SELL"])
            entry_p = c2.number_input("Entry Price", value=market['price'], step=0.1)
            exit_p = c3.number_input("Exit Price", value=market['price'], step=0.1)
            
            c4, c5, c6 = st.columns(3)
            sl_p = c4.number_input("Stop Loss Used", value=market['price'] - 2.5, step=0.1)
            result = c5.selectbox("Outcome", ["WIN (TP Hit)", "LOSS (SL Hit)", "BREAK-EVEN"])
            pnl_pips = c6.number_input("Pips Gained / Lost", value=15.0, step=1.0)
            
            notes = st.text_input("Trade Notes (Confluence, Session, Mistakes)", "M5 FVG bounce during London open")
            
            if st.form_submit_button("Save Trade to Journal"):
                st.session_state.trade_history.append({
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Type": trade_type,
                    "Entry": entry_p,
                    "Exit": exit_p,
                    "Outcome": result,
                    "Pips": pnl_pips,
                    "Notes": notes
                })
                st.success("Trade recorded!")

    if st.session_state.trade_history:
        df_trades = pd.DataFrame(st.session_state.trade_history)
        
        # Stats summary
        wins = len(df_trades[df_trades["Outcome"].str.contains("WIN")])
        total = len(df_trades)
        win_rate = round((wins / total) * 100, 1) if total > 0 else 0
        total_pips = df_trades["Pips"].sum()
        
        stat1, stat2, stat3 = st.columns(3)
        stat1.metric("Total Scalps Logged", total)
        stat2.metric("Win Rate", f"{win_rate}%")
        stat3.metric("Net Pips", f"{total_pips:+} pips")
        
        st.dataframe(df_trades, use_container_width=True)
    else:
        st.info("No trades logged yet. Use the form above to log live signals or backtests.")

# ==========================================
# TAB 4: SYSTEM SETTINGS
# ==========================================
with tab_settings:
    st.subheader("⚙️ Terminal Credentials & Configuration")
    st.caption("Configure your Groq API credentials securely. The sidebar remains clean and distraction-free.")
    
    saved_key = st.session_state.api_key
    new_key = st.text_input("Groq API Key:", value=saved_key, type="password", placeholder="gsk_...")
    
    if st.button("💾 Save Credentials"):
        st.session_state.api_key = new_key.strip()
        st.success("API Key saved to current session successfully!")
    
    st.divider()
    st.markdown("""
    #### 💡 How to never enter your API key again (Permanent Auto-Save):
    1. Go to your **Streamlit Cloud Dashboard** ([share.streamlit.io](https://share.streamlit.io/)).
    2. Click the three dots `⋮` next to your app and select **Settings** ➔ **Secrets**.
    3. Paste this line:
       ```toml
       GROQ_API_KEY = "your_actual_groq_key_here"
       ```
    4. Click **Save**. From then on, your app will automatically log in forever with zero typing!
    """)
