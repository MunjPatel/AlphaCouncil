# import streamlit as st
# import plotly.graph_objects as go
# import plotly.express as px
# import yfinance as yf
# import pandas as pd
# import numpy as np
# import json
# from groq import Groq

# # 1. CONFIGURATION
# st.set_page_config(page_title="Multi-Asset Analysis", page_icon="⚔️", layout="wide")

# # Professional Styling
# st.markdown("""
#     <style>
#     .stApp { background-color: #0e1117; }
    
#     /* AI Strategy Card Styling */
#     .ai-card {
#         background-color: #1f2937; 
#         border: 1px solid #374151;
#         border-left: 5px solid #8b5cf6; /* Purple for Strategy */
#         border-radius: 8px;
#         padding: 20px;
#         margin-top: 10px;
#         color: #f3f4f6;
#         font-family: 'Inter', sans-serif;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
#     }
#     .ai-header {
#         font-weight: 600;
#         color: #a78bfa;
#         margin-bottom: 10px;
#         font-size: 1.1em;
#     }
#     </style>
# """, unsafe_allow_html=True)

# st.title("⚔️ Multi-Asset Quantitative Strategy")

# # 2. DATA LOADING
# @st.cache_data
# def load_tickers():
#     try:
#         with open("sector_tickers.json", "r") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {}

# # 3. AI AGENT FUNCTION
# def generate_portfolio_ai_analysis(api_key, tickers, correlations, risk_return):
#     if not api_key:
#         return "⚠️ Please provide an API Key to unlock AI Analysis."
    
#     client = Groq(api_key=api_key)
    
#     # Summarize data for the LLM
#     corr_summary = correlations.to_string()
#     risk_summary = risk_return.to_string()
    
#     prompt = f"""
#     You are a Portfolio Manager at a Hedge Fund.
#     Analyze this multi-asset portfolio based on the data below:
    
#     Assets: {tickers}
    
#     1. Risk/Return Profile (Annualized):
#     {risk_summary}
    
#     2. Correlation Matrix:
#     {corr_summary}
    
#     Task:
#     Write a "Portfolio Strategy Memo" (max 150 words).
#     - Identify the asset with the best Risk-Adjusted Return.
#     - Identify any dangerous concentrations (High Correlation > 0.8).
#     - Suggest a diversification move or a hedge from any one of the following .
    
#     Format: Use HTML formatting for bolding (<b>) and lists (<ul><li>). Do not use Markdown.
#     IMPORTANT: Do NOT include a title like "Portfolio Strategy Memo". Start directly with the analysis text.
#     """
    
#     try:
#         completion = client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             max_tokens=400
#         )
#         return completion.choices[0].message.content
#     except Exception as e:
#         return f"AI Error: {e}"

# # 4. INITIALIZATION & SIDEBAR
# tickers_map = load_tickers()

# # Flatten dictionary for dropdown
# flat_ticker_list = {}
# for sector, assets in tickers_map.items():
#     for name, symbol in assets.items():
#         label = f"{name} ({symbol})"
#         flat_ticker_list[label] = symbol

# st.sidebar.header("⚙️ Portfolio Config")

# # API Key Logic
# api_key = st.secrets.get("GROQ_API_KEY")
# if not api_key:
#     api_key = st.sidebar.text_input("🔑 Groq API Key", type="password")

# # --- FIX FOR THE CRASH ---
# # 1. Define ideal defaults based on your specific JSON content
# ideal_defaults = [
#     "NVIDIA (NVDA)", 
#     "Microsoft (MSFT)", 
#     "Tesla (TSLA)" 
# ]

# # 2. Filter: Only keep defaults that actually exist in the generated list
# # This prevents the "StreamlitAPIException" if a ticker is missing from the JSON
# valid_defaults = [x for x in ideal_defaults if x in flat_ticker_list.keys()]

# # 3. If validation removed everything, just pick the first available option
# if not valid_defaults and flat_ticker_list:
#     valid_defaults = [list(flat_ticker_list.keys())[0]]

# selected_labels = st.sidebar.multiselect(
#     "Select Assets to Compare",
#     options=list(flat_ticker_list.keys()),
#     default=valid_defaults
# )

# timeframe = st.sidebar.selectbox("Lookback Period", ["1mo", "3mo", "6mo", "1y", "5y"], index=2)

# # 5. EXECUTION ENGINE
# if len(selected_labels) > 0:
#     selected_tickers = [flat_ticker_list[label] for label in selected_labels]
    
#     with st.spinner("Fetching market data..."):
#         # Fetch data
#         data = yf.download(selected_tickers, period=timeframe)['Close']
    
#     # Handle Data Structure (Series vs DataFrame)
#     if isinstance(data, pd.Series):
#         data = data.to_frame()
#         # If it's a series, yfinance might name the col 'Close' or the Ticker
#         if data.columns[0] == 'Close':
#             data.columns = selected_tickers
    
#     # Drop any rows that are all NaN (market holidays mismatch)
#     data.dropna(how='all', inplace=True)

#     if not data.empty:
#         # Calculations
#         # 1. Normalized Performance (Growth of $100)
#         normalized_data = (data / data.iloc[0]) * 100
        
#         # 2. Daily Returns
#         daily_returns = data.pct_change().dropna()
        
#         # 3. Annualized Stats
#         summary = pd.DataFrame()
#         summary['Return'] = daily_returns.mean() * 252 * 100
#         summary['Volatility'] = daily_returns.std() * (252**0.5) * 100
        
#         # --- VISUALS ---
        
#         # Chart 1: Performance
#         st.markdown("### 📈 Relative Performance")
#         fig_perf = go.Figure()
#         for col in normalized_data.columns:
#             fig_perf.add_trace(go.Scatter(
#                 x=normalized_data.index, 
#                 y=normalized_data[col], 
#                 mode='lines', 
#                 name=col
#             ))
#         fig_perf.update_layout(
#             height=450, 
#             paper_bgcolor='rgba(0,0,0,0)', 
#             plot_bgcolor='rgba(0,0,0,0)', 
#             hovermode="x unified",
#             xaxis=dict(showgrid=False),
#             yaxis=dict(showgrid=True, gridcolor='#374151', title="Value ($)")
#         )
#         st.plotly_chart(fig_perf, use_container_width=True)
        
#         col1, col2 = st.columns(2)
        
#         # Chart 2: Correlation Heatmap
#         with col1:
#             st.markdown("### 🔗 Correlation Matrix")
#             corr_matrix = daily_returns.corr()
#             fig_corr = px.imshow(
#                 corr_matrix, 
#                 text_auto=".2f", 
#                 color_continuous_scale='RdBu_r', 
#                 zmin=-1, zmax=1,
#                 aspect="auto"
#             )
#             fig_corr.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
#             st.plotly_chart(fig_corr, use_container_width=True)
            
#         # Chart 3: Risk/Reward Scatter
#         with col2:
#             st.markdown("### ⚖️ Efficient Frontier")
#             fig_risk = px.scatter(
#                 summary, 
#                 x='Volatility', 
#                 y='Return', 
#                 text=summary.index, 
#                 size=[20]*len(summary), 
#                 color='Return',
#                 color_continuous_scale='Viridis'
#             )
#             fig_risk.update_traces(textposition='top center')
#             fig_risk.update_layout(
#                 height=400, 
#                 paper_bgcolor='rgba(0,0,0,0)', 
#                 plot_bgcolor='rgba(0,0,0,0)',
#                 xaxis=dict(title="Annualized Volatility (Risk) %"),
#                 yaxis=dict(title="Annualized Return %")
#             )
#             st.plotly_chart(fig_risk, use_container_width=True)

#         # --- AI STRATEGY SECTION ---
#         st.divider()
        
#         col_ai_btn, col_spacer = st.columns([1, 4])
#         with col_ai_btn:
#             ai_btn = st.button("🧠 Generate Portfolio Strategy")
        
#         if ai_btn:
#             with st.spinner("Analyzing portfolio mathematics..."):
#                 # Pass the calculated stats to the AI
#                 analysis = generate_portfolio_ai_analysis(
#                     api_key, 
#                     selected_tickers, 
#                     corr_matrix, 
#                     summary
#                 )
                
#                 st.markdown(f"""
#                 <div class="ai-card">
#                     <div class="ai-header">🤖 AI Portfolio Architect</div>
#                     {analysis}
#                 </div>
#                 """, unsafe_allow_html=True)
#     else:
#         st.error("No data found for the selected tickers/timeframe.")

# else:
#     st.info("👈 Select assets from the sidebar to begin.")

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
import numpy as np
import json
from groq import Groq

# 1. CONFIGURATION
st.set_page_config(page_title="Multi-Asset Analysis", page_icon="⚔️", layout="wide")

# Professional Styling
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    
    /* AI Strategy Card Styling */
    .ai-card {
        background-color: #1f2937; 
        border: 1px solid #374151;
        border-left: 5px solid #8b5cf6; /* Purple for Strategy */
        border-radius: 8px;
        padding: 20px;
        margin-top: 10px;
        color: #f3f4f6;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .ai-header {
        font-weight: 600;
        color: #a78bfa;
        margin-bottom: 10px;
        font-size: 1.1em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚔️ Multi-Asset Quantitative Strategy")

# 2. DATA LOADING
@st.cache_data
def load_tickers():
    try:
        with open("sector_tickers.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# 3. AI AGENT FUNCTION (Updated for Universe Constraint)
def generate_portfolio_ai_analysis(api_key, tickers, correlations, risk_return, universe_map):
    if not api_key:
        return "⚠️ Please provide an API Key to unlock AI Analysis."
    
    client = Groq(api_key=api_key)
    
    # Summarize data for the LLM
    corr_summary = correlations.to_string()
    risk_summary = risk_return.to_string()
    
    # Format the universe for the prompt (Sector: Ticker list)
    universe_str = ""
    for sector, assets in universe_map.items():
        # Create string like "Tech: MSFT, AAPL, NVDA..."
        ticker_list = ", ".join([f"{symbol}" for name, symbol in assets.items()])
        universe_str += f"- {sector}: {ticker_list}\n"

    prompt = f"""
    You are a Portfolio Manager at a Hedge Fund.
    Analyze this multi-asset portfolio based on the data below:
    
    Current Portfolio Assets: {tickers}
    
    1. Risk/Return Profile (Annualized):
    {risk_summary}
    
    2. Correlation Matrix:
    {corr_summary}
    
    Task:
    Write a "Portfolio Strategy Memo" (max 150 words).
    - Identify the asset with the best Risk-Adjusted Return.
    - Identify any dangerous concentrations (High Correlation > 0.8).
    - Suggest a diversification move or a hedge. **You MUST choose a specific ticker from the following allowed universe**:
    
    ALLOWED UNIVERSE FOR HEDGING:
    {universe_str}
    
    Format: Use HTML formatting for bolding (<b>) and lists (<ul><li>). Do not use Markdown.
    IMPORTANT: Do NOT include a title like "Portfolio Strategy Memo". Start directly with the analysis text.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

# 4. INITIALIZATION & SIDEBAR
tickers_map = load_tickers()

# Flatten dictionary for dropdown
flat_ticker_list = {}
for sector, assets in tickers_map.items():
    for name, symbol in assets.items():
        label = f"{name} ({symbol})"
        flat_ticker_list[label] = symbol

st.sidebar.header("⚙️ Portfolio Config")

# API Key Logic
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("🔑 Groq API Key", type="password")

# --- DEFAULT SELECTION LOGIC ---
ideal_defaults = [
    "NVIDIA (NVDA)", 
    "Microsoft (MSFT)", 
    "Tesla (TSLA)" 
]
# Filter to ensure defaults exist in loaded JSON
valid_defaults = [x for x in ideal_defaults if x in flat_ticker_list.keys()]
if not valid_defaults and flat_ticker_list:
    valid_defaults = [list(flat_ticker_list.keys())[0]]

selected_labels = st.sidebar.multiselect(
    "Select Assets to Compare",
    options=list(flat_ticker_list.keys()),
    default=valid_defaults
)

timeframe = st.sidebar.selectbox("Lookback Period", ["1mo", "3mo", "6mo", "1y", "5y"], index=2)

# 5. EXECUTION ENGINE
if len(selected_labels) > 0:
    selected_tickers = [flat_ticker_list[label] for label in selected_labels]
    
    with st.spinner("Fetching market data..."):
        # Fetch data
        data = yf.download(selected_tickers, period=timeframe)['Close']
    
    # Handle Data Structure
    if isinstance(data, pd.Series):
        data = data.to_frame()
        if data.columns[0] == 'Close':
            data.columns = selected_tickers
    
    data.dropna(how='all', inplace=True)

    if not data.empty:
        # Calculations
        normalized_data = (data / data.iloc[0]) * 100
        daily_returns = data.pct_change().dropna()
        
        # Stats
        summary = pd.DataFrame()
        summary['Return'] = daily_returns.mean() * 252 * 100
        summary['Volatility'] = daily_returns.std() * (252**0.5) * 100
        
        # --- VISUALS ---
        st.markdown("### 📈 Relative Performance (Rebased to 100)")
        fig_perf = go.Figure()
        for col in normalized_data.columns:
            fig_perf.add_trace(go.Scatter(
                x=normalized_data.index, y=normalized_data[col], mode='lines', name=col
            ))
        fig_perf.update_layout(
            height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            hovermode="x unified", xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#374151', title="Value ($)")
        )
        st.plotly_chart(fig_perf, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔗 Correlation Matrix")
            corr_matrix = daily_returns.corr()
            fig_corr = px.imshow(
                corr_matrix, text_auto=".2f", color_continuous_scale='RdBu_r', zmin=-1, zmax=1, aspect="auto"
            )
            fig_corr.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_corr, use_container_width=True)
            
        with col2:
            st.markdown("### ⚖️ Efficient Frontier")
            fig_risk = px.scatter(
                summary, x='Volatility', y='Return', text=summary.index, 
                size=[20]*len(summary), color='Return', color_continuous_scale='Viridis'
            )
            fig_risk.update_traces(textposition='top center')
            fig_risk.update_layout(
                height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title="Annualized Volatility (Risk) %"), yaxis=dict(title="Annualized Return %")
            )
            st.plotly_chart(fig_risk, use_container_width=True)

        # --- AI STRATEGY SECTION ---
        st.divider()
        
        col_ai_btn, col_spacer = st.columns([1, 4])
        with col_ai_btn:
            ai_btn = st.button("🧠 Generate Portfolio Strategy")
        
        if ai_btn:
            with st.spinner("Analyzing portfolio mathematics..."):
                # Pass the stats AND the tickers_map (Universe)
                analysis = generate_portfolio_ai_analysis(
                    api_key, 
                    selected_tickers, 
                    corr_matrix, 
                    summary,
                    tickers_map 
                )
                
                st.markdown(f"""
                <div class="ai-card">
                    <div class="ai-header">🤖 AI Portfolio Architect</div>
                    {analysis}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("No data found for the selected tickers/timeframe.")

else:
    st.info("👈 Select assets from the sidebar to begin.")