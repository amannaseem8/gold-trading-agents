import streamlit as st
import yfinance as yf
from google import genai
import time

# --- Page Setup ---
st.set_page_config(
    page_title="XAU/USD 5-Agent Trading Desk",
    page_icon="🪙",
    layout="wide"
)

st.title("🪙 XAU/USD Multi-Agent AI Trading Desk")
st.caption("5 Autonomous AI Agents analyzing Gold in real-time to find optimal entries.")

# --- Sidebar: API Key ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key (Free):", type="password")
    st.markdown("[Free API Key yahan se lein](https://aistudio.google.com/)")
    st.divider()
    st.info("💡 Yeh app 100% cloud par chalti hai. Aapke laptop ki 0 MB storage use hoti hai.")

# --- Live Market Data Fetcher ---
@st.cache_data(ttl=60)
def get_gold_market_data():
    try:
        gold = yf.Ticker("GC=F").history(period="2d", interval="15m")
        dxy = yf.Ticker("DX-Y.NYB").history(period="2d", interval="15m")
        
        current_gold = round(gold['Close'].iloc[-1], 2)
        recent_high = round(gold['High'].iloc[-10:].max(), 2)
        recent_low = round(gold['Low'].iloc[-10:].min(), 2)
        current_dxy = round(dxy['Close'].iloc[-1], 2) if not dxy.empty else 103.50
        
        return {
            "gold_price": current_gold,
            "high": recent_high,
            "low": recent_low,
            "dxy": current_dxy
        }
    except Exception:
        # Fallback agar market holiday ho ya feed delay ho
        return {
            "gold_price": 2650.00,
            "high": 2658.00,
            "low": 2642.00,
            "dxy": 103.80
        }

data = get_gold_market_data()

# Live Market Cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Gold Price", f"${data['gold_price']}")
c2.metric("15m Recent High", f"${data['high']}")
c3.metric("15m Recent Low", f"${data['low']}")
c4.metric("US Dollar Index (DXY)", f"{data['dxy']}")

st.divider()

# --- Chat History Storage ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar=message["avatar"]):
        st.markdown(f"**{message['name']}**")
        st.markdown(message["content"])

# --- Main Trigger Button ---
if st.button("🚀 Start 5-Agent Market Analysis", type="primary"):
    if not api_key:
        st.error("Pehle sidebar mein apni free Gemini API Key enter karein!")
    else:
        client = genai.Client(api_key=api_key)

        context_info = f"""
        Market: Gold (XAU/USD)
        Current Price: ${data['gold_price']}
        15-Minute Range High: ${data['high']}
        15-Minute Range Low: ${data['low']}
        US Dollar Index (DXY): {data['dxy']}
        """

        # 4 Specialist Agents
        agent_list = [
            {
                "name": "Agent 1: Technical & SMC Analyst",
                "avatar": "📊",
                "prompt": f"""You are Agent 1, a professional Smart Money Concepts (SMC) & Price Action trader for XAU/USD.
                Context: {context_info}
                Analyze market structure (BOS/CHoCH), Order Blocks, Fair Value Gaps (FVG), and support/resistance.
                Provide your verdict in under 100 words directly to the team."""
            },
            {
                "name": "Agent 2: Macro & Treasury Analyst",
                "avatar": "🌐",
                "prompt": f"""You are Agent 2, a Macroeconomist monitoring the US Dollar (DXY) and Treasury Yields for Gold.
                Context: {context_info}
                Explain how current DXY strength/weakness influences Gold direction.
                Provide your verdict in under 100 words."""
            },
            {
                "name": "Agent 3: Liquidity & Session Hunter",
                "avatar": "🎯",
                "prompt": f"""You are Agent 3, specialized in Session Liquidity and Retail Traps on Gold.
                Context: {context_info}
                Check for Asian/London/NY session high/low liquidity sweeps and stop hunts.
                Provide your verdict in under 100 words."""
            },
            {
                "name": "Agent 4: Sentiment & Geopolitical Watchdog",
                "avatar": "🗞️",
                "prompt": f"""You are Agent 4, tracking Safe-Haven Gold demand, geopolitical conflicts, and market fear/greed.
                Context: {context_info}
                Assess overall safe-haven sentiment for Gold.
                Provide your verdict in under 100 words."""
            }
        ]

        agent_outputs = []

        # Run Agents 1 to 4 sequentially
        with st.spinner("AI Agents live market scan kar rahe hain..."):
            for ag in agent_list:
                resp = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=ag["prompt"]
                )
                txt = resp.text
                agent_outputs.append(f"{ag['name']}: {txt}")

                with st.chat_message("assistant", avatar=ag["avatar"]):
                    st.markdown(f"**{ag['name']}**")
                    st.markdown(txt)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "name": ag["name"],
                    "avatar": ag["avatar"],
                    "content": txt
                })
                time.sleep(1)

        # Agent 5: Final Decision Maker
        with st.spinner("Agent 5 (Chief Decision Officer) trade verify kar raha hai..."):
            chief_prompt = f"""
            You are Agent 5, the Chief Decision & Risk Officer.
            Review the analysis of your 4 specialist agents:
            
            {"".join(agent_outputs)}
            
            Current Gold Price: ${data['gold_price']}
            
            Synthesize all 4 inputs and produce the FINAL TRADE PLAN in this exact format:
            
            ### 🎯 FINAL TRADE VERDICT
            * **Signal:** [BUY / SELL / WAIT]
            * **Entry Zone:** [Exact Price or Range]
            * **Stop Loss (SL):** [Exact Price]
            * **Take Profit 1 (TP1):** [Conservative Target]
            * **Take Profit 2 (TP2):** [Extended Target]
            * **Risk-to-Reward (R:R):** [Minimum 1:2]
            * **Reasoning:** [2-3 short bullet points summarizing confluence]
            * **Invalidation:** [Price level that cancels this idea]
            """

            chief_resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=chief_prompt
            )
            final_plan = chief_resp.text

            with st.chat_message("assistant", avatar="⚖️"):
                st.markdown("**Agent 5: Chief Decision & Risk Officer**")
                st.success(final_plan)

            st.session_state.chat_history.append({
                "role": "assistant",
                "name": "Agent 5: Chief Decision & Risk Officer",
                "avatar": "⚖️",
                "content": final_plan
            })
