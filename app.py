import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import yfinance as yf
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import bcrypt
import os
from entry_functions import log_trade 

# --- CONFIG & STYLING ---
st.set_page_config(page_title="MD Journal", layout="wide")

# --- 1. LOAD CONFIGURATION ---
CONFIG_FILE = 'config.yaml'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        # Create default config if missing
        default_config = {
            'credentials': {'usernames': {}},
            'cookie': {'expiry_days': 30, 'key': 'random_key', 'name': 'trade_cookie'}
        }
        with open(CONFIG_FILE, 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False)
            
    with open(CONFIG_FILE) as file:
        return yaml.load(file, Loader=SafeLoader)

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

config = load_config()

# --- 2. AUTHENTICATION HANDLER ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- 3. LOGIN / REGISTER UI ---
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None

# Only show Login/Register if NOT logged in
if st.session_state["authentication_status"] is not True:
    
    # Create Tabs for Toggle
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])
    
    with tab1:
        authenticator.login(location='main')
        
        if st.session_state["authentication_status"] is False:
            st.error('Username/password is incorrect')
        elif st.session_state["authentication_status"] is None:
            st.warning('Please enter your username and password')

    with tab2:
        st.subheader("Create New Profile")
        with st.form("register_form"):
            new_user = st.text_input("Username").lower().strip()
            new_name = st.text_input("Full Name")
            new_pass = st.text_input("Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            
            reg_submit = st.form_submit_button("Sign Up")
            
            if reg_submit:
                if new_pass != confirm_pass:
                    st.error("Passwords do not match!")
                elif new_user in config['credentials']['usernames']:
                    st.error("Username already exists!")
                elif len(new_pass) < 3:
                    st.error("Password must be at least 3 characters.")
                else:
                    # Hash the password
                    hashed_pw = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                    
                    # Update Config
                    config['credentials']['usernames'][new_user] = {
                        'name': new_name,
                        'password': hashed_pw
                    }
                    save_config(config)
                    st.success("Account created! Please go to the Login tab.")

# --- STOP EXECUTION IF NOT LOGGED IN ---
if st.session_state["authentication_status"] is not True:
    st.stop()

# =========================================================
#  APP STARTS HERE (Only for Logged In Users)
# =========================================================

# Get user details
name = st.session_state["name"]
username = st.session_state["username"]

st.sidebar.write(f"Welcome, **{name}**! 👋")
authenticator.logout('Logout', 'sidebar')

# Define the user's personal file path
USER_CSV = os.path.join("user_profiles", f"{username}_journal.csv")

def load_custom_css():
    st.markdown("""
        <style>
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
    
    1.  **Entry Date:** This triggers the *Market Context* search.
    2.  **Trade Status:** * **Closed:** You bought and sold.
        * **Open (Active):** You are still holding.
    3.  **Conviction Notes:** Write *why*. "RSI was oversold..."
    """)

# --- 2. SIDEBAR: DATA ENTRY ---
st.sidebar.header("Log New Trade")

with st.sidebar.form("trade_form"):
    ticker = st.text_input("Ticker Symbol", value="NVDA")
    direction = st.selectbox("Direction", ["Long", "Short"])
    shares = st.number_input("Quantity (Shares)", min_value=1, value=10, step=1)
    
    st.markdown("### 📅 Timing")
    trade_status = st.radio("Status", ["Closed (Complete)", "Open (Active)"], horizontal=True)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        entry_date = st.date_input("Entry Date")
    with col_d2:
        exit_date = st.date_input("Exit Date", value=entry_date)

    st.markdown("### 💰 Execution")
    col1, col2 = st.columns(2)
    with col1:
        entry_price = st.number_input("Entry Price", min_value=0.0, format="%.2f")
    with col2:
        exit_price = st.number_input("Exit Price", min_value=0.0, format="%.2f")
    
    st.markdown("### 📝 Analysis")
    notes = st.text_area("Conviction / Notes", placeholder="E.g., Bought off the 200SMA support.")

    submit = st.form_submit_button("Log Trade")

    if submit:
        e_date_str = entry_date.strftime("%Y-%m-%d")
        
        if trade_status == "Closed (Complete)":
            x_date_str = exit_date.strftime("%Y-%m-%d")
            final_exit_price = exit_price
        else:
            x_date_str = "Active"
            final_exit_price = 0.0
            
        with st.spinner("Saving to secure profile..."):
            try:
                log_trade(e_date_str, x_date_str, ticker, entry_price, final_exit_price, shares, direction, notes, username)
                st.success(f"Trade Logged for {username}: {ticker}")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 3. MAIN DASHBOARD ---
st.subheader(f"{name}'s Performance")

try:
    df = pd.read_csv(USER_CSV) 
    
    if "Entry_Date" in df.columns:
        df["Entry_Date"] = pd.to_datetime(df["Entry_Date"])
        df = df.sort_values("Entry_Date", ascending=False)
    
    # --- LIVE PORTFOLIO UPDATER ---
    active_mask = df["Exit_Date"] == "Active"
    
    if active_mask.any():
        st.caption("🔴 Live Updating Active Positions...")
        df['Exit_Date'] = df['Exit_Date'].astype(str)

        for index, row in df[active_mask].iterrows():
            ticker = row['Ticker']
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.fast_info['last_price']
                
                df.at[index, 'Exit_Price'] = current_price 
                df.at[index, 'Exit_Date'] = "LIVE"
                
                entry_price = row['Entry_Price']
                direction = row['Direction'].lower()
                
                if entry_price > 0:
                    if direction == "long":
                        unrealized_pnl = (current_price - entry_price) / entry_price
                    else: # Short
                        unrealized_pnl = (entry_price - current_price) / entry_price
                    
                    df.at[index, 'PnL_Percent'] = unrealized_pnl
            except Exception:
                pass 

    # --- METRICS SECTION ---
    if not df.empty:
        colA, colB, colC = st.columns(3)
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
        display_df = df.copy()
        display_df['PnL_Percent'] = display_df['PnL_Numeric'].apply(lambda x: f"{x*100:.2f}%")
        
        display_cols = ["Entry_Date", "Ticker", "Direction", "Quantity", "Entry_Price", "Exit_Price", "PnL_Percent", "PnL_Dollar", "Market_Regime", "VIX", "10Y_Yield", "Notes", "Exit_Date"]
        final_cols = [c for c in display_cols if c in display_df.columns]
        st.dataframe(display_df[final_cols], use_container_width=True)

    # --- 4. ANALYTICS BUTTON ---
        st.markdown("---")
        st.subheader("🕵️‍♂️ Trade Surveillance")
        from analytics import get_paper_hands_score, get_macro_stats
        if st.button("Run Deep Analysis"):
            with st.spinner("Analyzing historical data..."):
                st.markdown("### 1. The 'Macro Filter'")
                macro_stats = get_macro_stats(df)
                if macro_stats:
                    cols = st.columns(len(macro_stats))
                    for i, (regime, data) in enumerate(macro_stats.items()):
                        with cols[i]:
                            st.metric(f"{regime} Win Rate", data['Win Rate'], f"{data['Trades']} Trades")
                else:
                    st.info("Not enough data for Macro Analysis.")

                st.markdown("### 2. The 'Paper Hands' Score (14 Days Later)")
                missed_gains = get_paper_hands_score(df)
                analysis_df = df[['Entry_Date', 'Ticker', 'Exit_Date']].copy()
                analysis_df['Change in Stock Price'] = missed_gains
                st.table(analysis_df)

except FileNotFoundError:
    st.info(f"Welcome {name}! No trades logged yet. Use the sidebar to add your first one!")