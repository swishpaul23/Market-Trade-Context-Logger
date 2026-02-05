import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

def get_market_context(trade_date_str):
    target_date = datetime.strptime(trade_date_str, "%Y-%m-%d")
    
    # Look back 400 days to ensure we have enough data for 200SMA
    start_date = target_date - timedelta(days=400)
    end_date = target_date + timedelta(days=1) 
    
    tickers = ["SPY", "^VIX", "^TNX"]
    
    print(f"Fetching data...")
    # 1. Download data
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)
    
    # --- THE FIX IS HERE ---
    # yfinance returns data like: [('Close', 'SPY'), ('Close', '^VIX')...]
    # We strictly want the 'Close' prices to make the table simple (1-Level)
    if isinstance(data.columns, pd.MultiIndex):
        try:
            # Try to grab 'Adj Close' first (accounts for dividends), fallback to 'Close'
            data = data['Adj Close'] if 'Adj Close' in data.columns.levels[0] else data['Close']
        except KeyError:
            # If the structure is different, force grab 'Close'
            data = data['Close']
            
    # Now the columns are just ["SPY", "^TNX", "^VIX"] - plain strings.
    # -----------------------

    # 2. Calculate Indicators
    # Now this line works because "SPY" is a simple column name
    data['SPY_200SMA'] = data['SPY'].rolling(window=200).mean()
    
    # 3. Handle Weekends/Holidays (The "asof" lookup)
    # We sort index to ensure 'asof' works correctly
    data = data.sort_index()
    
    # Find the index location of the target date (or the previous available day)
    try:
        idx = data.index.get_indexer([target_date], method='pad')[0]
        
        # If the index is -1, it means we requested a date before our data starts
        if idx == -1:
            return {"Error": "Date out of range (too old)"}
            
        day_data = data.iloc[idx]
        found_date = data.index[idx]

        # Safety Check: If the "closest" date is > 5 days ago, data is missing
        if (target_date - found_date).days > 5:
             return {"Error": "Market data missing for this week"}

        # 4. Build Context
        context = {
            "Context_Date": found_date.strftime("%Y-%m-%d"),
            "SPY_Price": round(float(day_data['SPY']), 2),
            "SPY_200SMA": round(float(day_data['SPY_200SMA']), 2),
            "VIX": round(float(day_data['^VIX']), 2),
            "10Y_Yield": round(float(day_data['^TNX']), 2),
            "Market_Regime": "Bullish" if day_data['SPY'] > day_data['SPY_200SMA'] else "Bearish"
        }
        
        return context

    except Exception as e:
        return {"Error": f"Lookup failed: {str(e)}"}

def calculate_performance(entry, exit, position_type):
    """
    Docstring for calculate_performance: Calculates the performance of a particular trade
    
    :param entry: Entry price for trade
    :param exit: Exit price for trade
    :param position_type: Long or Short

    """
    if entry == 0: return 0.0
    
    direction = position_type.lower()
    if direction == "long":
        return round((exit-entry) / entry, 4)
    elif direction == "short":
        return round((entry-exit) / entry,4)
    else:
        print(f"Warning: Unknown direction '{position_type}'. Assuming long.")
        return round((exit - entry) / entry, 4)

def log_trade(date, ticker, entry, exit, direction, journal_file="trading_journal.csv"):
    """
     Docstring for log_trade
     FUNCTION C: THE CONTROLLER (Log & Save)
    """
    print(f"\n--- Processing Trade: {ticker} on {date} ---")

    # 1. GENERATE ID
    # Format: YYYYMMDD_TICKER_DIR (e.g., 20260205_NVDA_LONG)
    clean_date = date.replace("-", "")
    trade_id = f"{clean_date}_{ticker.upper()}_{direction.upper()}"
    
    # 2. GET CONTEXT (Function A)
    print("Fetching Market Context...")
    context = get_market_context(date)
    
    if context is None:
        print("CRITICAL ERROR: Context is None")
        return  # <--- STOPS the function here.

    # 3. CALCULATE STATS (Function B)
    pnl_pct = calculate_performance(entry, exit, direction)

    # 4. BUILD THE ROW
    trade_data = {
        "Trade_ID": trade_id,
        "Date": date,
        "Ticker": ticker.upper(),
        "Direction": direction.upper(),
        "Entry_Price": entry,
        "Exit_Price": exit,
        "PnL_Percent": pnl_pct,
        # Unpack the context dictionary here
        "SPY_Price": context['SPY_Price'],
        "Market_Regime": context['Market_Regime'],
        "VIX": context['VIX'],
        "10Y_Yield": context['10Y_Yield']
    }
    
    # 5. SAVE TO CSV
    df = pd.DataFrame([trade_data])
    
    # Check if file exists to determine if we need a header
    if not os.path.exists(journal_file):
        df.to_csv(journal_file, index=False)
        print(f"Created new journal: {journal_file}")
    else:
        # Append mode ('a'), header=False
        df.to_csv(journal_file, mode='a', header=False, index=False)
        print(f"Trade appended to {journal_file}")

    print("Success.")
    print("-" * 30)

if __name__ == "__main__":
# You must call the function with a test trade
    log_trade("2026-02-03", "NVDA", 120.00, 125.00, "Long")