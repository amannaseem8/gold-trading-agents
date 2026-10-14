import streamlit as st
import yfinance as yf
from groq import Groq
import time

# --- Page Setup ---
st.set_page_config(
    page_title="XAU/USD 5-Agent Trading Desk",
    page_icon="🪙",
    layout="wide"
)

st.title("🪙 XAU/USD Multi-Agent AI Trading Desk (Powered by Groq)")
st.caption("Ultra-fast autonomous AI agents powered by Llama 3.1 Instant.")

# --- Sidebar: Groq API Key ---
with st.sidebar:
    st.header("⚙️ Configuration")
    raw_api_key = st.text_input("Groq API Key (Free):", type="password")
    api_key = raw_api_key.strip() if raw_api_key else ""
    st.markdown("[Free Groq Key yahan se lein](https://console.groq.com/)")
    st.divider()
    st.success("⚡ Powered by Groq LPU: Instant 800 tokens/sec speed!")

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

# --- Chat History ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar=message["avatar"]):
        st.markdown(f"**{message['name']}**")
        st.markdown(message["content"])

# --- Helper: Query Groq with Fallback ---
def call_groq_agent(client, prompt):
    candidate_models = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768"
    ]
    last_err = None
    for model_name in candidate_models:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an elite quantitative analyst specializing in Gold (XAU/USD)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=250
            )
            return completion.choices[0].message.content
        except Exception as e:
            last_err = e
            continue
    raise last_err

# --- Trigger Analysis ---
if st.button("🚀 Start 5-Agent Market Analysis", type="primary"):
    if not api_key:
        st.error("Pehle sidebar mein apni free Groq API Key enter karein!")
    else:
        try:
            client = Groq(api_key=api_key)

            context_info = f"""
            Asset: Gold (XAU/USD)
            Live Price: ${data['gold_price']}
            Recent 15m High: ${data['high']}
            Recent 15m Low: ${data['low']}
            US Dollar Index (DXY): {data['dxy']}
            """

            agent_list = [
                {
                    "name": "Agent 1: Technical & SMC Analyst",
                    "avatar": "📊",
                    "prompt": f"Analyze XAU/USD market structure (BOS/CHoCH), Order Blocks, and Fair Value Gaps (FVG). Context: {context_info}. Be concise, institutional, and direct under 80 words."
                },
                {
                    "name": "Agent 2: Macro & Treasury Analyst",
                    "avatar": "🌐",
                    "prompt": f"Explain the direct impact of DXY ({data['dxy']}) and US Treasury yields on Gold right now. Context: {context_info}. Concise verdict under 80 words."
                },
                {
                    "name": "Agent 3: Liquidity & Session Hunter",
                    "avatar": "🎯",
                    "prompt": f"Identify session liquidity sweeps (Asian/London/NY high/low), fakeouts, and stop hunts. Context: {context_info}. Concise verdict under 80 words."
                },
                {
                    "name": "Agent 4: Sentiment & Geopolitical Watchdog",
                    "avatar": "🗞️",
                    "prompt": f"Assess safe-haven demand, central bank buying, and geopolitical risk premium on Gold. Context: {context_info}. Concise verdict under 80 words."
                }
            ]

            agent_outputs = []

            for ag in agent_list:
                with st.spinner(f"{ag['name']} analysis kar raha hai..."):
                    txt = call_groq_agent(client, ag["prompt"])
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
                    time.sleep(0.3)

            # Agent 5: Master Risk Manager
            with st.spinner("Agent 5 (Chief Decision Officer) final trade setup nikaal raha hai..."):
                chief_prompt = f"""
                You are Agent 5, Chief Decision & Risk Officer.
                Synthesize all 4 specialist reports:
                {"".join(agent_outputs)}
                Current Gold Price: ${data['gold_price']}
                
                Produce the FINAL TRADE PLAN strictly in this format:
                ### 🎯 FINAL TRADE VERDICT
                * **Signal:** [BUY / SELL / WAIT]
                * **Entry Zone:** [Exact Price Range]
                * **Stop Loss (SL):** [Exact Price]
                * **Take Profit 1 (TP1):** [Conservative Target]
                * **Take Profit 2 (TP2):** [Runner Target]
                * **Risk-to-Reward (R:R):** [Minimum 1:2]
                * **Reasoning:** [2 bullet points based on team consensus]
                * **Invalidation:** [Level that cancels setup]
                """

                final_plan = call_groq_agent(client, chief_prompt)

                with st.chat_message("assistant", avatar="⚖️"):
                    st.markdown("**Agent 5: Chief Decision & Risk Officer**")
                    st.success(final_plan)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "name": "Agent 5: Chief Decision & Risk Officer",
                    "avatar": "⚖️",
                    "content": final_plan
                })

        except Exception as e:
            st.error(f"Error: {str(e)}")
