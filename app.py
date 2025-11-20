import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
import numpy as np
import json
from groq import Groq  # <--- ADDED BACK THE AI AGENT

# 1. CONFIG
st.set_page_config(page_title="Multi-Asset Analysis", page_icon="⚔️", layout="wide")

# Professional Styling (Same as Dashboard)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .ai-card {
        background-color: #1f2937; 
        border: 1px solid #374151;
        border-left: 5px solid #8b5cf6; /* Purple for Strategy */
        border-radius: 8px;
        padding: 20px;
        margin-top: 10px;
        color: #f3f4f6;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚔️ Multi-Asset Quantitative Strategy")


# 2. LOAD DATA HELPER
@st.cache_data
def load_tickers():
    with open("sector_tickers.json", "r") as f:
        return json.load(f)


tickers_map = load_tickers()
flat_ticker_list = {}
for sector, assets in tickers_map.items():
    for name, symbol in assets.items():
        label = f"{name} ({symbol})"
        flat_ticker_list[label] = symbol


# 3. AI AGENT FUNCTION (The Missing Piece)
def generate_portfolio_ai_analysis(api_key, tickers, correlations, risk_return):
    if not api_key:
        return "⚠️ Please provide an API Key to unlock AI Analysis."

    client = Groq(api_key=api_key)

    # We summarize the data for the LLM to keep the prompt concise
    # Convert correlation matrix to a string summary
    corr_summary = correlations.to_string()
    risk_summary = risk_return.to_string()

    prompt = f"""
    You are a Portfolio Manager at a Hedge Fund.
    Analyze this multi-asset portfolio based on the data below:

    Assets: {tickers}

    1. Risk/Return Profile (Annualized):
    {risk_summary}

    2. Correlation Matrix:
    {corr_summary}

    Task:
    Write a "Portfolio Strategy Memo" (max 150 words).
    - Identify the asset with the best Risk-Adjusted Return.
    - Identify any dangerous concentrations (High Correlation > 0.8).
    - Suggest a diversification move.

    Format: Use bullet points. Be direct and sophisticated.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=2,
            max_tokens=300
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Ercror: {e}"


# 4. SIDEBAR CONTROLS
st.sidebar.header("⚙️ Portfolio Config")

# API Key Logic
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("🔑 Groq API Key", type="password")

selected_labels = st.sidebar.multiselect(
    "Select Assets to Compare",
    options=list(flat_ticker_list.keys()),
    default=["NVIDIA Corp. (NVDA)", "Bitcoin USD (BTC-USD)", "S&P 500 (^GSPC)"]
)
timeframe = st.sidebar.selectbox("Lookback Period", ["1mo", "3mo", "6mo", "1y", "5y"], index=3)

# 5. EXECUTION ENGINE
if len(selected_labels) > 0:
    selected_tickers = [flat_ticker_list[label] for label in selected_labels]

    with st.spinner("Fetching data..."):
        data = yf.download(selected_tickers, period=timeframe)['Close']

    if isinstance(data, pd.Series):
        data = data.to_frame()

    # Calculations
    normalized_data = (data / data.iloc[0]) * 100
    daily_returns = data.pct_change().dropna()

    # Stats for AI
    summary = pd.DataFrame()
    summary['Return'] = daily_returns.mean() * 252 * 100
    summary['Volatility'] = daily_returns.std() * (252 ** 0.5) * 100

    # --- VISUALS ---
    st.markdown("### 📈 Relative Performance")
    fig_perf = go.Figure()
    for col in normalized_data.columns:
        fig_perf.add_trace(go.Scatter(x=normalized_data.index, y=normalized_data[col], mode='lines', name=col))
    fig_perf.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           hovermode="x unified")
    st.plotly_chart(fig_perf, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔗 Correlation Matrix")
        corr_matrix = daily_returns.corr()
        fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
        fig_corr.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_corr, use_container_width=True)

    with col2:
        st.markdown("### ⚖️ Efficient Frontier (Risk vs Return)")
        fig_risk = px.scatter(summary, x='Volatility', y='Return', text=summary.index, size=[20] * len(summary),
                              color='Return')
        fig_risk.update_traces(textposition='top center')
        fig_risk.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_risk, use_container_width=True)

    # --- AI STRATEGY SECTION ---
    st.divider()
    st.subheader("🤖 AI Portfolio Architect")

    if st.button("Generate Strategy Memo"):
        with st.spinner("Analyzing correlations and risk profile..."):
            # Pass the calculated stats to the AI
            analysis = generate_portfolio_ai_analysis(
                api_key,
                selected_tickers,
                corr_matrix,
                summary
            )

            st.markdown(f"""
            <div class="ai-card">
                <h4>🧠 Portfolio Strategy</h4>
                {analysis}
            </div>
            """, unsafe_allow_html=True)

else:
    st.info("👈 Select assets from the sidebar to begin.")