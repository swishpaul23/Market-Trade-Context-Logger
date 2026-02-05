import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from entry_functions import log_trade

# --- CONFIG & STYLING ---
st.set_page_config(page_title="MD Journal", layout="wide")
st.title("📊 Institutional Trading Journal")

def load_custom_css():
    st.markdown("""
        <style>
        .stApp { background-color: #2E1A47; }
        [data-testid="stSidebar"] { background-color: #1F1135; border-right: 1px solid #663399; }
        [data-testid="stMetric"] { background-color: rgba(102, 51, 153, 0.2); border: 1px solid #A3779D; border-radius: 10px; color: #E6C7E6; }
        .stTextInput > div > div > input, .stTextArea > div > div > textarea { background-color: #1F1135; color: #E6C7E6; border: 1px solid #663399; }
        h1, h2, h3, p, li { color: #E6C7E6 !important; font-family: 'Helvetica Neue', sans-serif; }
        </style>
    """, unsafe_allow_html=True)

load_custom_css()

# --- 1. THE "MD" GUIDE ---
with st.expander("📘 How to use this Journal (The MD Framework)"):
    st.markdown("""
    **The Goal:** Move from "Random Gambling" to "Data-Driven Alpha."
    
    1.  **Entry Date:** This triggers the *Market Context* search. We want to know if you bought when the VIX was high (Fear) or low (Greed).
    2.  **Swing Trades:** Check the box if you held overnight. This helps track if you are better at *scalping* (Day Trade) or *position trading* (Swing).
    3.  **Conviction Notes:** Don't just write "I bought." Write *why*. "RSI was oversold AND Apple announced a buyback."
    4.  **Interpretation:** * **Win Rate vs. VIX:** Are you losing money when volatility is high? Stop trading on red days.
        * **Equity Curve:** Is your line jagged (high risk) or smooth (consistent)?
    """)

# --- 2. SIDEBAR: DATA ENTRY ---
st.sidebar.header("Log New Trade")

with st.sidebar.form("trade_form"):
    # Basic Info
    ticker = st.text_input("Ticker Symbol", value="NVDA")
    direction = st.selectbox("Direction", ["Long", "Short"])
    
    # Date Logic
    st.markdown("### 📅 Timing")
    entry_date = st.date_input("Entry Date")
    
    # Swing Trade Logic
    is_swing = st.checkbox("Is this a Swing Trade? (Held Overnight)")
    
    if is_swing:
        exit_date = st.date_input("Exit Date", value=entry_date)
    else:
        # For Day Trades, Exit = Entry
        exit_date = entry_date 
        st.caption("*Day Trade: Exit Date set to Entry Date automatically.*")

    # Prices
    st.markdown("### 💰 Execution")
    col1, col2 = st.columns(2)
    with col1:
        entry_price = st.number_input("Entry Price", min_value=0.0, format="%.2f")
    with col2:
        exit_price = st.number_input("Exit Price", min_value=0.0, format="%.2f")
    
    # Notes
    st.markdown("### 📝 Analysis")
    notes = st.text_area("Conviction / Notes", placeholder="E.g., Bought off the 200SMA support. Market was oversold.")

    # Submit
    submit = st.form_submit_button("Log Trade")

    if submit:
        e_date_str = entry_date.strftime("%Y-%m-%d")
        x_date_str = exit_date.strftime("%Y-%m-%d")
        
        with st.spinner("Fetching Market Context..."):
            try:
                log_trade(e_date_str, x_date_str, ticker, entry_price, exit_price, direction, notes)
                st.success(f"Trade Logged: {ticker}")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 3. MAIN DASHBOARD ---
st.subheader("Recent Performance")

try:
    df = pd.read_csv("trading_journal.csv")
    
    # Sort by Entry Date
    if "Entry_Date" in df.columns:
        df["Entry_Date"] = pd.to_datetime(df["Entry_Date"])
        df = df.sort_values("Entry_Date", ascending=False)
    
    # METRICS
    if not df.empty:
        colA, colB, colC = st.columns(3)
        total_pnl = df["PnL_Percent"].mean() * 100
        win_rate = len(df[df["PnL_Percent"] > 0]) / len(df) * 100
        
        colA.metric("Avg Return", f"{total_pnl:.2f}%")
        colB.metric("Win Rate", f"{win_rate:.0f}%")
        colC.metric("Total Trades", len(df))

        # --- SEABORN VISUALIZATION (Equity Curve) ---
        st.markdown("---")
        st.subheader("📈 Performance Trajectory")
        
        # Create Cumulative PnL for the chart
        chart_df = df.sort_values("Entry_Date", ascending=True).copy()
        chart_df["Cumulative Return"] = chart_df["PnL_Percent"].cumsum() * 100
        chart_df["Trade Number"] = range(1, len(chart_df) + 1)
        
        # Seaborn Plot
        fig, ax = plt.subplots(figsize=(10, 4))
        # Dark theme background for plot
        fig.patch.set_facecolor('#2E1A47')
        ax.set_facecolor('#1F1135')
        
        # The Line
        sns.lineplot(data=chart_df, x="Trade Number", y="Cumulative Return", ax=ax, color="#E6C7E6", linewidth=2.5, marker="o")
        
        # The Zero Line (Breakeven)
        ax.axhline(0, color="#A3779D", linestyle="--", alpha=0.5)
        
        # Styling
        ax.set_title("Cumulative Return (%)", color="#E6C7E6")
        ax.set_xlabel("Trade Count", color="#E6C7E6")
        ax.set_ylabel("Return %", color="#E6C7E6")
        ax.tick_params(colors="#E6C7E6")
        for spine in ax.spines.values():
            spine.set_edgecolor("#663399")
            
        st.pyplot(fig)
        
        # --- DATA TABLE ---
        st.markdown("### 📋 Trade Log")
        # Reorder columns for readability
        display_cols = ["Entry_Date", "Ticker", "Direction", "PnL_Percent", "Notes", "Market_Regime"]
        # Only show cols that actually exist (avoids errors if CSV is old)
        final_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[final_cols], use_container_width=True)

except FileNotFoundError:
    st.info("No trades logged yet. Use the sidebar to add your first one!")