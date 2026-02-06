import pandas as pd
import yfinance as yf
import os
from datetime import datetime

# --- HELPER: GET MARKET CONTEXT ---
def get_market_context(date_str):
    """
    Fetches VIX, SPY 200SMA, and 10Y Yield for a given date.
    Returns a dictionary or None if fetch fails.
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # 1. Get VIX (Volatility)
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(start=target_date, period="5d")
        vix_val = round(vix_hist['Close'].iloc[0], 2) if not vix_hist.empty else 0.0
        
        # 2. Get SPY (Market Trend)
        spy = yf.Ticker("SPY")
        # We need enough data to calculate a 200-day Moving Average (approx 300 days lookback)
        start_date = target_date - pd.Timedelta(days=300)
        spy_hist = spy.history(start=start_date, end=target_date)
        
        if spy_hist.empty:
            return None
            
        current_price = spy_hist['Close'].iloc[-1]
        sma_200 = spy_hist['Close'].rolling(window=200).mean().iloc[-1]
        
        regime = "Bullish" if current_price > sma_200 else "Bearish"
        
        # 3. Get 10Y Yield (Macro)
        tnx = yf.Ticker("^TNX")
        tnx_hist = tnx.history(start=target_date, period="5d")
        yield_val = round(tnx_hist['Close'].iloc[0], 2) if not tnx_hist.empty else 0.0
        
        return {
            "VIX": vix_val,
            "Market_Regime": regime,
            "10Y_Yield": yield_val,
            "SPY_Price": round(current_price, 2)
        }
    except Exception as e:
        print(f"Error fetching context: {e}")
        # Return default values instead of None to prevent crashing
        return {
            "VIX": 0.0,
            "Market_Regime": "Unknown",
            "10Y_Yield": 0.0,
            "SPY_Price": 0.0
        }

# --- HELPER: CALC PnL ---
def calculate_performance(entry, exit, direction):
    if entry == 0: return 0.0
    if exit == 0: return 0.0 # Active trade
    
    direction = direction.lower()
    if direction == "long":
        return round((exit - entry) / entry, 4)
    elif direction == "short":
        return round((entry - exit) / entry, 4)
    else:
        return 0.0

# --- MAIN LOGGING FUNCTION ---
def log_trade(entry_date, exit_date, ticker, entry, exit, shares, direction, notes, username):
    print(f"\n--- Processing Trade for {username}: {ticker} ---")
    
    # 1. SETUP FILE PATH
    if not os.path.exists("user_profiles"):
        os.makedirs("user_profiles")
    journal_file = os.path.join("user_profiles", f"{username}_journal.csv")
    
    # 2. GENERATE ID
    clean_date = entry_date.replace("-", "")
    trade_id = f"{clean_date}_{ticker.upper()}_{direction.upper()}"
    
    # 3. GET CONTEXT
    # We now handle errors inside the helper, so it always returns a dict (not None)
    context = get_market_context(entry_date)
    
    # 4. CALCULATE STATS
    pnl_pct = calculate_performance(entry, exit, direction)
    
    pnl_dollar = 0.0
    if exit > 0:
        if direction.lower() == "long":
            pnl_dollar = (exit - entry) * shares
        else:
            pnl_dollar = (entry - exit) * shares

    # 5. BUILD ROW (The 'trade_data' variable must be created HERE, unindented)
    trade_data = {
        "Trade_ID": trade_id,
        "Entry_Date": entry_date,
        "Exit_Date": exit_date,
        "Ticker": ticker.upper(),
        "Direction": direction.upper(),
        "Quantity": shares,
        "Entry_Price": entry,
        "Exit_Price": exit,
        "PnL_Percent": pnl_pct,
        "PnL_Dollar": round(pnl_dollar, 2),
        "Notes": notes,
        "Market_Regime": context['Market_Regime'],
        "VIX": context['VIX'],
        "10Y_Yield": context['10Y_Yield']
    }
    
    # 6. SAVE TO FILE
    # This block is now safely OUTSIDE any 'if' statements
    df = pd.DataFrame([trade_data])
    
    if not os.path.exists(journal_file):
        df.to_csv(journal_file, index=False)
        print(f"Created new profile: {journal_file}")
    else:
        df.to_csv(journal_file, mode='a', header=False, index=False)
        print(f"Trade appended to {journal_file}")

    print("Success.")