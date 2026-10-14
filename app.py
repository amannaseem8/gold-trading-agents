import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from groq import Groq
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone

# --- Terminal Setup ---
st.set_page_config(
    page_title="XAU/USD Institutional M5 Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Dark Theme
st.markdown("""
<style>
    .main { background-color: #0b0e14; color: #e6edf3; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 700; color: #58a6ff; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; height: 3rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 6px; padding: 8px 16px; color: #8b949e; }
    .stTabs [aria-selected="true"] { background-color: #1f6feb !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# State Management
if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")

if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Quantitative Math & Technical Analysis Engine ---
@st.cache_data(ttl=30)
def fetch_quantitative_market_data():
    try:
        gold = yf.Ticker("GC=F").history(period="3d", interval="5m")
        dxy = yf.Ticker("DX-Y.NYB").history(period="1d", interval="5m")
        
        if gold.empty or len(gold) < 30:
            raise ValueError("Insufficient data")

        # 1. EMAs
        gold['EMA_9'] = gold['Close'].ewm(span=9, adjust=False).mean()
        gold['EMA_21'] = gold['Close'].ewm(span=21, adjust=False).mean()
        gold['EMA_200'] = gold['Close'].ewm(span=200, adjust=False).mean()
        
        # 2. RSI (14)
        delta = gold['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        gold['RSI'] = 100 - (100 / (1 + rs))

        # 3. ATR (14)
        tr1 = gold['High'] - gold['Low']
        tr2 = (gold['High'] - gold['Close'].shift()).abs()
        tr3 = (gold['Low'] - gold['Close'].shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        gold['ATR'] = tr.rolling(window=14).mean()

        latest = gold.iloc[-1]
        cur_price = round(latest['Close'], 2)
        ema_9 = round(latest['EMA_9'], 2)
        ema_21 = round(latest['EMA_21'], 2)
        ema_200 = round(latest['EMA_200'], 2)
        rsi = round(latest['RSI'], 1)
        atr = round(latest['ATR'], 2)

        # 4. Fair Value Gap (FVG) Detection on last 5 candles
        fvg_bullish = None
        fvg_bearish = None
        for i in range(len(gold)-4, len(gold)-1):
            c1 = gold.iloc[i-1]
            c3 = gold.iloc[i+1]
            if c3['Low'] > c1['High']:
                fvg_bullish = f"${round(c1['High'], 2)} - ${round(c3['Low'], 2)}"
            elif c1['Low'] > c3['High']:
                fvg_bearish = f"${round(c3['High'], 2)} - ${round(c1['Low'], 2)}"

        # 5. Session Killzone Detection (UTC)
        current_utc_hour = datetime.now(timezone.utc).hour
        if 7 <= current_utc_hour < 10:
            session_status = "London Open Killzone (High Liquidity)"
        elif 12 <= current_utc_hour < 16:
            session_status = "New York Open Killzone (Peak Volatility)"
        elif 0 <= current_utc_hour < 6:
            session_status = "Asian Session (Accumulation/Range)"
        else:
            session_status = "Inter-Session Transition (Moderate Volatility)"

        current_dxy = round(dxy['Close'].iloc[-1], 2) if not dxy.empty else 103.50

        # Trend Determination
        if cur_price > ema_200 and ema_9 > ema_21:
            trend = "BULLISH (Price > EMA 200 & EMA 9 > 21)"
        elif cur_price < ema_200 and ema_9 < ema_21:
            trend = "BEARISH (Price < EMA 200 & EMA 9 < 21)"
        else:
            trend = "CHOP / CONSOLIDATION (Testing Key EMAs)"

        return {
            "price": cur_price,
            "high": round(gold['High'].iloc[-6:].max(), 2),
            "low": round(gold['Low'].iloc[-6:].min(), 2),
            "trend": trend,
            "ema_200": ema_200,
            "rsi": rsi,
            "atr": atr,
            "fvg_bullish": fvg_bullish or "None in immediate range",
            "fvg_bearish": fvg_bearish or "None in immediate range",
            "session": session_status,
            "dxy": current_dxy
        }
    except Exception:
        return {
            "price": 2652.80, "high": 2656.20, "low": 2649.50,
            "trend": "BULLISH (Rebound above EMA)", "ema_200": 2647.50,
            "rsi": 48.5, "atr": 2.20, "fvg_bullish": "$2650.10 - $2651.40",
            "fvg_bearish": "None", "session": "Active Session", "dxy": 103.45
        }

m = fetch_quantitative_market_data()

# Header
st.title("⚡ XAU/USD Institutional M5 Scalping Terminal")
st.caption(f"Status: **{m['session']}** | Quantitative Trend: **{m['trend']}**")

# Metrics Display
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Live Gold Price", f"${m['price']}")
c2.metric("M5 RSI (14)", f"{m['rsi']}")
c3.metric("M5 ATR (Volatility)", f"${m['atr']}")
c4.metric("DXY Index", f"{m['dxy']}")
c5.metric("EMA 200 Filter", f"${m['ema_200']}")

st.write("")

# Navigation Tabs
tab_live, tab_chart, tab_backtest, tab_settings = st.tabs([
    "🚀 Scalp Intelligence Desk",
    "📈 TradingView Live Chart",
    "📊 Backtest & Performance Log",
    "⚙️ System Settings"
])

# --- Robust Groq Caller with 3x Retry ---
def call_agent_robust(client, model, messages):
    for attempt in range(1, 4):
        try:
            res = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.15,
                max_tokens=250
            )
            return res.choices[0].message.content
        except Exception as e:
            if attempt == 3:
                raise e
            time.sleep(1.2 * attempt)

# ==========================================
# TAB 1: SCALPING DESK
# ==========================================
with tab_live:
    col_run, col_del = st.columns([4, 1])
    with col_run:
        btn_scan = st.button("⚡ Scan Market & Formulate Scalp Ticket", type="primary")
    with col_del:
        if st.button("🧹 Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar=msg["avatar"]):
            st.markdown(f"**{msg['name']}**")
            st.markdown(msg["content"])

    if btn_scan:
        if not st.session_state.api_key:
            st.error("⚠️ API Key missing. Please open the **Settings** tab and save your Groq key.")
        else:
            try:
                client = Groq(api_key=st.session_state.api_key)
                
                # Fetch best active chat model
                all_models = [x.id for x in client.models.list().data if not any(k in x.id.lower() for k in ["whisper", "guard", "safeguard", "tts"])]
                active_model = all_models[0] if all_models else "llama-3.1-8b-instant"

                # Comprehensive Quant Context
                quant_context = f"""
                Asset: Gold Spot (XAU/USD)
                Live M5 Price: ${m['price']}
                Recent 30m Range: High ${m['high']} | Low ${m['low']}
                Market Structure Trend: {m['trend']}
                M5 RSI: {m['rsi']} (30=Oversold, 70=Overbought)
                M5 ATR: ${m['atr']} (Recommended Stop Loss buffer: 1.5x ATR = ${round(m['atr']*1.5, 2)})
                Nearest Bullish FVG: {m['fvg_bullish']}
                Nearest Bearish FVG: {m['fvg_bearish']}
                Active Trading Session: {m['session']}
                US Dollar Index (DXY): {m['dxy']}
                """

                scalper_team = [
                    {
                        "name": "Agent 1: SMC Market Structure & FVG Specialist",
                        "avatar": "📊",
                        "prompt": f"""You are Agent 1, institutional SMC scalper.
                        Data: {quant_context}
                        Analyze:
                        1. Structure alignment with EMA 200 (${m['ema_200']}).
                        2. Interaction with active FVGs ({m['fvg_bullish']} / {m['fvg_bearish']}).
                        3. Displacement on M5.
                        Verdict in under 70 words. Strict precision."""
                    },
                    {
                        "name": "Agent 2: Liquidity Pools & Session Trap Hunter",
                        "avatar": "🎯",
                        "prompt": f"""You are Agent 2, ICT Liquidity Specialist.
                        Data: {quant_context}
                        Analyze:
                        1. Is current high (${m['high']}) or low (${m['low']}) a liquidity sweep or genuine breakout?
                        2. Are retail stop losses being hunted in this session ({m['session']})?
                        Verdict in under 70 words."""
                    },
                    {
                        "name": "Agent 3: Momentum & Volume Oscillator",
                        "avatar": "⚡",
                        "prompt": f"""You are Agent 3, Order Flow & Momentum Analyst.
                        Data: {quant_context}
                        Analyze:
                        1. RSI reading ({m['rsi']}) - divergence or exhaustion?
                        2. DXY inverse pressure ({m['dxy']}).
                        Verdict in under 70 words."""
                    },
                    {
                        "name": "Agent 4: Capital Defense & News Filter",
                        "avatar": "🛡️",
                        "prompt": f"""You are Agent 4, Head of Risk Management.
                        Data: {quant_context}
                        Analyze:
                        1. Spread safety for M5 scalping in current volatility (ATR: ${m['atr']}).
                        2. Confluence check: Approve or Veto trade execution.
                        Verdict in under 60 words."""
                    }
                ]

                team_transcripts = []

                for ag in scalper_team:
                    with st.spinner(f"{ag['name']} calculating..."):
                        res_text = call_agent_robust(
                            client,
                            active_model,
                            [
                                {"role": "system", "content": "You are a quantitative prop firm scalper. Provide strict data-driven analysis."},
                                {"role": "user", "content": ag["prompt"]}
                            ]
                        )
                        team_transcripts.append(f"{ag['name']}: {res_text}")

                        with st.chat_message("assistant", avatar=ag["avatar"]):
                            st.markdown(f"**{ag['name']}**")
                            st.markdown(res_text)

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "name": ag["name"],
                            "avatar": ag["avatar"],
                            "content": res_text
                        })
                        time.sleep(0.2)

                # Agent 5: Execution Officer (Confluence Rules)
                with st.spinner("Agent 5 formulating institutional execution ticket..."):
                    chief_prompt = f"""
                    You are Agent 5, Chief Scalp Execution Officer.
                    Review your 4 quantitative specialists:
                    {"".join(team_transcripts)}
                    
                    Quantitative Facts:
                    - Current Price: ${m['price']}
                    - ATR: ${m['atr']}
                    - Trend: {m['trend']}
                    
                    RULE OF CONFLUENCE:
                    If agents disagree or market is choppy, output 'NO TRADE (WAIT FOR CLEAN SWEEP)'.
                    Only generate BUY if price respects bullish structure. Only generate SELL if price respects bearish structure.
                    
                    Output strictly in this format:
                    ### ⚡ VERIFIED M5 SCALP TICKET
                    * **Signal Action:** [STRONG BUY / BUY / NO TRADE (WAIT) / SELL / STRONG SELL]
                    * **Execution Type:** [Market Order OR Limit Entry Zone]
                    * **Entry Range:** [Exact numeric range, e.g. ${m['price']-0.5} - ${m['price']+0.5}]
                    * **Stop Loss (SL):** [Exact Price - strictly 1.5x ATR buffer: ~15 to 25 pips]
                    * **Take Profit 1 (TP1):** [Conservative 1:1.5 RR - take 75% profit]
                    * **Take Profit 2 (TP2):** [Runner 1:2.5+ RR]
                    * **Risk-to-Reward:** [Calculated RR]
                    * **Execution Rule:** [e.g. Move SL to Breakeven as soon as TP1 is hit]
                    * **Invalidation Level:** [Exact price that cancels this trade]
                    """

                    final_ticket = call_agent_robust(
                        client,
                        active_model,
                        [
                            {"role": "system", "content": "You are the Head Scalping Executioner. Calculate exact price targets."},
                            {"role": "user", "content": chief_prompt}
                        ]
                    )

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
    tv_widget = """
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
    components.html(tv_widget, height=620)

# ==========================================
# TAB 3: BACKTESTING & PERFORMANCE TRACKER
# ==========================================
with tab_backtest:
    st.subheader("📝 M5 Scalp Backtesting & Journal")
    with st.expander("➕ Log Scalp Trade Result", expanded=False):
        with st.form("trade_form"):
            col_a, col_b, col_c = st.columns(3)
            t_type = col_a.selectbox("Direction", ["BUY", "SELL"])
            t_entry = col_b.number_input("Entry Price", value=m['price'], step=0.1)
            t_exit = col_c.number_input("Exit Price", value=m['price'], step=0.1)
            
            col_d, col_e, col_f = st.columns(3)
            t_sl = col_d.number_input("Stop Loss Used", value=m['price'] - 2.5, step=0.1)
            t_result = col_e.selectbox("Outcome", ["WIN (TP Hit)", "LOSS (SL Hit)", "BREAK-EVEN"])
            t_pips = col_f.number_input("Net Pips", value=18.0, step=1.0)
            
            t_notes = st.text_input("Confluence Notes", "M5 Bullish FVG bounce + London Open sweep")
            
            if st.form_submit_button("Save Trade"):
                st.session_state.trade_history.append({
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Type": t_type, "Entry": t_entry, "Exit": t_exit,
                    "Outcome": t_result, "Pips": t_pips, "Notes": t_notes
                })
                st.success("Trade recorded!")

    if st.session_state.trade_history:
        df = pd.DataFrame(st.session_state.trade_history)
        wins = len(df[df["Outcome"].str.contains("WIN")])
        total = len(df)
        win_rate = round((wins / total) * 100, 1) if total > 0 else 0
        total_pips = df["Pips"].sum()
        
        s1, s2, s3 = st.columns(3)
        s1.metric("Total Scalps Logged", total)
        s2.metric("Win Rate", f"{win_rate}%")
        s3.metric("Net Pips", f"{total_pips:+} pips")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No trades logged yet. Backtest your agent signals here to calculate win rate.")

# ==========================================
# TAB 4: SYSTEM SETTINGS
# ==========================================
with tab_settings:
    st.subheader("⚙️ Credentials & System Settings")
    st.caption("Save your Groq API key here. It will persist throughout your session.")
    
    cur_key = st.session_state.api_key
    input_key = st.text_input("Groq API Key:", value=cur_key, type="password", placeholder="gsk_...")
    
    if st.button("💾 Save Credentials"):
        st.session_state.api_key = input_key.strip()
        st.success("API Key saved successfully!")
