import streamlit as st
import pandas as pd
from entry_functions import log_trade  # This imports YOUR function!

# --- ADD THIS TO app.py ---
def load_custom_css():
    st.markdown("""
        <style>
        /* 1. Main Background Force */
        .stApp {
            background-color: #2E1A47;
        }
        
        /* 2. Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #1F1135; /* Darker Midnight Plum */
            border-right: 1px solid #663399;
        }

        /* 3. Metrics Cards (Glass Effect) */
        [data-testid="stMetric"] {
            background-color: rgba(102, 51, 153, 0.2); /* Royal Amethyst with transparency */
            border: 1px solid #A3779D; /* Soft Violet Border */
            padding: 15px;
            border-radius: 10px;
            color: #E6C7E6;
        }

        /* 4. Input Fields & Buttons */
        .stTextInput > div > div > input {
            background-color: #1F1135;
            color: #E6C7E6;
            border: 1px solid #663399;
        }
        
        /* 5. Dataframe Header Color */
        thead tr th:first-child {display:none}
        tbody th {display:none}
        .stDataFrame { border: 1px solid #663399; }
        
        /* 6. Titles and Headers */
        h1, h2, h3 {
            color: #E6C7E6 !important;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 200;
        }
        </style>
    """, unsafe_allow_html=True)

# CALL THE FUNCTION RIGHT AFTER SET_PAGE_CONFIG
# st.set_page_config(...) <--- You already have this line
load_custom_css() # <--- Add this line

# --- CONFIGURATION ---
st.set_page_config(page_title="MD Journal", layout="wide")
st.title("📊 Institutional Trading Journal")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("Log New Trade")

with st.sidebar.form("trade_form"):
    # Input fields
    ticker = st.text_input("Ticker Symbol", value="NVDA")
    trade_date = st.date_input("Trade Date")
    direction = st.selectbox("Direction", ["Long", "Short"])
    
    col1, col2 = st.columns(2)
    with col1:
        entry_price = st.number_input("Entry Price", min_value=0.0, format="%.2f")
    with col2:
        exit_price = st.number_input("Exit Price", min_value=0.0, format="%.2f")
        
    # The Button
    submit = st.form_submit_button("Log Trade")

    if submit:
        # 1. Convert date to string (Your backend expects "YYYY-MM-DD")
        date_str = trade_date.strftime("%Y-%m-%d")
        
        # 2. Call your backend function
        with st.spinner("Fetching Market Context..."):
            try:
                # We call the function from backend.py
                log_trade(date_str, ticker, entry_price, exit_price, direction)
                st.success(f"Trade Logged: {ticker}")
            except Exception as e:
                st.error(f"Error: {e}")

# --- MAIN PAGE: DASHBOARD ---
st.subheader("Recent Trades")

try:
    # Load the CSV to show the data
    df = pd.read_csv("trading_journal.csv")
    
    # Sort by date (newest first) if 'Date' exists
    if "Date" in df.columns:
        df = df.sort_values("Date", ascending=False)
        
    # Display interactive table
    st.dataframe(df, use_container_width=True)
    
    # --- BONUS: INSTANT ANALYTICS ---
    # Simple metric to show it's working
    if not df.empty:
        colA, colB, colC = st.columns(3)
        total_pnl = df["PnL_Percent"].mean() * 100
        win_rate = len(df[df["PnL_Percent"] > 0]) / len(df) * 100
        
        colA.metric("Avg Return", f"{total_pnl:.2f}%")
        colB.metric("Win Rate", f"{win_rate:.0f}%")
        colC.metric("Total Trades", len(df))

except FileNotFoundError:
    st.info("No trades logged yet. Use the sidebar to add your first one!")