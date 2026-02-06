import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import yfinance as yf
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
    
    # NEW: Quantity Input
    shares = st.number_input("Quantity (Shares)", min_value=1, value=10, step=1) # <--- ADDED
    
    # Date Logic
    st.markdown("### 📅 Timing")
    trade_status = st.radio("Status", ["Closed (Complete)", "Open (Active)"], horizontal=True)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        entry_date = st.date_input("Entry Date")
    with col_d2:
        exit_date = st.date_input("Exit Date", value=entry_date)

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

    submit = st.form_submit_button("Log Trade")

    if submit:
        e_date_str = entry_date.strftime("%Y-%m-%d")
        
        if trade_status == "Closed (Complete)":
            x_date_str = exit_date.strftime("%Y-%m-%d")
            final_exit_price = exit_price
        else:
            x_date_str = "Active"
            final_exit_price = 0.0
            
        with st.spinner("Fetching Market Context..."):
            try:
                # PASS SHARES TO BACKEND
                log_trade(e_date_str, x_date_str, ticker, entry_price, final_exit_price, shares, direction, notes)
                st.success(f"Trade Logged: {ticker} ({shares} shares)")
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
    
    # --- LIVE PORTFOLIO UPDATER ---
    # This block checks for "Active" trades and updates their price in real-time
    active_mask = df["Exit_Date"] == "Active"
    
    if active_mask.any():
        st.caption("🔴 Live Updating Active Positions...")

        # 1. FORCE COLUMN TO STRING (Fixes the "Hidden" bug)
        df['Exit_Date'] = df['Exit_Date'].astype(str)

        # Iterate through active trades
        for index, row in df[active_mask].iterrows():
            ticker = row['Ticker']
            try:
                # Fast fetch of current price
                stock = yf.Ticker(ticker)
                current_price = stock.fast_info['last_price']
                
                # Update the dataframe IN MEMORY (doesn't save to CSV, just for display)
                df.at[index, 'Exit_Price'] = current_price # Show live price as exit
                df.at[index, 'Exit_Date'] = "LIVE"         # Mark as Live
                
                # Calculate Unrealized PnL
                entry_price = row['Entry_Price']
                direction = row['Direction'].lower()
                
                if entry_price > 0:
                    if direction == "long":
                        unrealized_pnl = (current_price - entry_price) / entry_price
                    else: # Short
                        unrealized_pnl = (entry_price - current_price) / entry_price
                    
                    df.at[index, 'PnL_Percent'] = unrealized_pnl
                    
            except Exception:
                pass # If fetch fails, just keep original data

    # --- METRICS SECTION ---
    if not df.empty:
        # Filter: We want to see stats for BOTH Closed and Live trades now
        # But we format the PnL to look nice
        
        colA, colB, colC = st.columns(3)
        
        # Calculate Stats (Handling numeric conversion safely)
        # We treat "Active" trades as having 0 PnL for the "Closed Win Rate", 
        # OR we can include them to see "Current Win Rate including Floating"
        
        # Let's clean the column for math
        df["PnL_Numeric"] = pd.to_numeric(df["PnL_Percent"], errors='coerce').fillna(0)
        
        total_pnl = df["PnL_Numeric"].mean() * 100
        win_rate = len(df[df["PnL_Numeric"] > 0]) / len(df) * 100
        
        colA.metric("Avg Return (inc. Unrealized)", f"{total_pnl:.2f}%")
        colB.metric("Win Rate", f"{win_rate:.0f}%")
        colC.metric("Total Trades", len(df))

        # --- SEABORN VISUALIZATION ---
        st.markdown("---")
        st.subheader("📈 Performance Trajectory")
        
        chart_df = df.sort_values("Entry_Date", ascending=True).copy()
        chart_df["Cumulative Return"] = chart_df["PnL_Numeric"].cumsum() * 100
        chart_df["Trade Number"] = range(1, len(chart_df) + 1)
        
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor('#2E1A47')
        ax.set_facecolor('#1F1135')
        
        # Plot
        sns.lineplot(data=chart_df, x="Trade Number", y="Cumulative Return", ax=ax, color="#E6C7E6", linewidth=2.5, marker="o")
        ax.axhline(0, color="#A3779D", linestyle="--", alpha=0.5)
        
        ax.set_title("Equity Curve (Real-Time)", color="#E6C7E6")
        ax.set_xlabel("Trade Count", color="#E6C7E6")
        ax.set_ylabel("Return %", color="#E6C7E6")
        ax.tick_params(colors="#E6C7E6")
        for spine in ax.spines.values():
            spine.set_edgecolor("#663399")
            
        st.pyplot(fig)
        
        # --- DATA TABLE ---
        st.markdown("### 📋 Trade Log")
        
        # Format PnL column to show %
        display_df = df.copy()
        display_df['PnL_Percent'] = display_df['PnL_Numeric'].apply(lambda x: f"{x*100:.2f}%")
        
        # Add 'Quantity' and 'PnL_Dollar' to this list
        display_cols = ["Entry_Date", "Ticker", "Direction", "Quantity", "Entry_Price", "Exit_Price", "PnL_Percent", "PnL_Dollar", "Market_Regime", "VIX", "10Y_Yield", "Notes", "Exit_Date"]
        
        final_cols = [c for c in display_cols if c in display_df.columns]
        st.dataframe(display_df[final_cols], use_container_width=True)

    # --- 4. ANALYTICS BUTTON (RESTORED) ---
        st.markdown("---")
        st.subheader("🕵️‍♂️ Trade Surveillance")
        
    # Import the logic we wrote in analytics.py
        from analytics import get_paper_hands_score, get_macro_stats
        if st.button("Run Deep Analysis"):
            with st.spinner("Analyzing historical data..."):
                
                # A. Macro Stats
                st.markdown("### 1. The 'Macro Filter'")
                macro_stats = get_macro_stats(df)
                if macro_stats:
                    cols = st.columns(len(macro_stats))
                    for i, (regime, data) in enumerate(macro_stats.items()):
                        with cols[i]:
                            st.metric(f"{regime} Win Rate", data['Win Rate'], f"{data['Trades']} Trades")
                else:
                    st.info("Not enough data for Macro Analysis.")

                # B. Paper Hands Score
                st.markdown("### 2. The 'Paper Hands' Score (14 Days Later)")
                st.info("Checks if you sold too early (Swing Trade Logic).")
                
                # Run the heavy math
                missed_gains = get_paper_hands_score(df)
                
                # Show results in a clean table
                analysis_df = df[['Entry_Date', 'Ticker', 'Exit_Date']].copy()
                analysis_df['Outcome'] = missed_gains
                st.table(analysis_df)

except FileNotFoundError:
    st.info("No trades logged yet. Use the sidebar to add your first one!")
