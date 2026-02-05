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
        /* Royal Amethyst Theme */
        .stApp { background-color: #2E1A47; }
        [data-testid="stSidebar"] { background-color: #1F1135; border-right: 1px solid #663399; }
        [data-testid="stMetric"] { background-color: rgba(102, 51, 153, 0.2); border: 1px solid #A3779D; border-radius: 10px; color: #E6C7E6; }
        .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stDateInput > div > div > input { 
            background-color: #1F1135; color: #E6C7E6; border: 1px solid #663399; 
        }
        .stSelectbox > div > div > div {
             background-color: #1F1135; color: #E6C7E6;
        }
        h1, h2, h3, p, li, span, label { color: #E6C7E6 !important; font-family: 'Helvetica Neue', sans-serif; }
        </style>
    """, unsafe_allow_html=True)

load_custom_css()

# --- 1. THE "MD" GUIDE ---
with st.expander("📘 How to use this Journal (The MD Framework)"):
    st.markdown("""
    **The Goal:** Move from "Random Gambling" to "Data-Driven Alpha."
    
    1.  **Entry Date:** This triggers the *Market Context* search. We want to know if you bought when the VIX was high (Fear) or low (Greed).
    2.  **Trade Status:** * **Closed:** You bought and sold. Select your Exit Date.
        * **Open (Active):** You are still holding. The system tracks it but won't calculate "Missed Gains" yet.
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
    
    # Status Selector
    trade_status = st.radio("Status", ["Closed (Complete)", "Open (Active)"], horizontal=True)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        entry_date = st.date_input("Entry Date")
    
    with col_d2:
        if trade_status == "Closed (Complete)":
            exit_date = st.date_input("Exit Date", value=entry_date)
        else:
            st.info("Holding...")
            exit_date = None

    # Prices
    st.markdown("### 💰 Execution")
    col1, col2 = st.columns(2)
    with col1:
        entry_price = st.number_input("Entry Price", min_value=0.0, format="%.2f")
    with col2:
        if trade_status == "Closed (Complete)":
            exit_price = st.number_input("Exit Price", min_value=0.0, format="%.2f")
        else:
            exit_price = 0.0 # Force 0 for active trades
    
    # Notes
    st.markdown("### 📝 Analysis")
    notes = st.text_area("Conviction / Notes", placeholder="E.g., Bought off the 200SMA support. Market was oversold.")

    # Submit Button
    submit = st.form_submit_button("Log Trade")

    if submit:
        e_date_str = entry_date.strftime("%Y-%m-%d")
        
        # Handle Open Trades
        if exit_date:
            x_date_str = exit_date.strftime("%Y-%m-%d")
        else:
            x_date_str = "Active"

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
        # Filter for CLOSED trades only for Win Rate
        closed_trades = df[df["Exit_Date"] != "Active"]
        
        colA, colB, colC = st.columns(3)
        
        if not closed_trades.empty:
            # Clean non-numeric PnL for calculation
            # (Sometimes PnL is NaN if calculation failed)
            valid_pnl = pd.to_numeric(closed_trades["PnL_Percent"], errors='coerce').fillna(0)
            
            total_pnl = valid_pnl.mean() * 100
            win_rate = len(valid_pnl[valid_pnl > 0]) / len(valid_pnl) * 100
            
            colA.metric("Avg Return", f"{total_pnl:.2f}%")
            colB.metric("Win Rate", f"{win_rate:.0f}%")
        else:
            colA.metric("Avg Return", "0.00%")
            colB.metric("Win Rate", "0%")
            
        colC.metric("Total Trades", len(df))

        # --- SEABORN VISUALIZATION (Equity Curve) ---
        if not closed_trades.empty:
            st.markdown("---")
            st.subheader("📈 Performance Trajectory")
            
            # Create Cumulative PnL for the chart
            chart_df = closed_trades.sort_values("Entry_Date", ascending=True).copy()
            chart_df["PnL_Numeric"] = pd.to_numeric(chart_df["PnL_Percent"], errors='coerce').fillna(0)
            chart_df["Cumulative Return"] = chart_df["PnL_Numeric"].cumsum() * 100
            chart_df["Trade Number"] = range(1, len(chart_df) + 1)
            
            # Seaborn Plot
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor('#2E1A47')
            ax.set_facecolor('#1F1135')
            
            sns.lineplot(data=chart_df, x="Trade Number", y="Cumulative Return", ax=ax, color="#E6C7E6", linewidth=2.5, marker="o")
            ax.axhline(0, color="#A3779D", linestyle="--", alpha=0.5)
            
            ax.set_title("Cumulative Return (%)", color="#E6C7E6")
            ax.set_xlabel("Trade Count", color="#E6C7E6")
            ax.set_ylabel("Return %", color="#E6C7E6")
            ax.tick_params(colors="#E6C7E6")
            for spine in ax.spines.values():
                spine.set_edgecolor("#663399")
                
            st.pyplot(fig)
        
        # --- DATA TABLE ---
        st.markdown("### 📋 Trade Log")
        display_cols = ["Entry_Date", "Ticker", "Direction", "PnL_Percent", "Notes", "Exit_Date"]
        final_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[final_cols], use_container_width=True)

    # --- 4. ANALYTICS BUTTON (Swing Trade Logic) ---
    st.markdown("---")
    st.subheader("🕵️‍♂️ Trade Surveillance")
    
    from analytics import get_paper_hands_score, get_macro_stats
    
    if st.button("Run Deep Analysis"):
        with st.spinner("Analyzing historical data..."):
            
            # Macro Stats
            st.markdown("### 1. The 'Macro Filter'")
            macro_stats = get_macro_stats(df)
            if macro_stats:
                cols = st.columns(len(macro_stats))
                for i, (regime, data) in enumerate(macro_stats.items()):
                    with cols[i]:
                        st.metric(f"{regime} Win Rate", data['Win Rate'], f"{data['Trades']} Trades")
            else:
                st.info("Not enough data for Macro Analysis.")

            # Paper Hands
            st.markdown("### 2. The 'Paper Hands' Score (14 Days Later)")
            st.info("Checks if you sold too early (Swing Trade Logic).")
            missed_gains = get_paper_hands_score(df)
            
            analysis_df = df[['Entry_Date', 'Ticker', 'Exit_Date']].copy()
            analysis_df['Outcome'] = missed_gains
            st.table(analysis_df)

except FileNotFoundError:
    st.info("No trades logged yet. Use the sidebar to add your first one!")