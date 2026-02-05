import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def get_paper_hands_score(df):
    """
    SWING TRADER VERSION:
    Checks the price 14 DAYS after your EXIT to see if you missed a trend continuation.
    """
    print("Running Swing Trader Surveillance...")
    results = []
    
    today = datetime.now().date()
    
    for index, row in df.iterrows():
        # 1. Safety Check: Do we have an Exit Date?
        if pd.isna(row.get('Exit_Date')) or row['Exit_Price'] == 0:
            results.append("Holding (Active)")
            continue
            
        # 2. Parse the EXIT Date (Critical for Swing Trading)
        try:
            exit_date = datetime.strptime(str(row['Exit_Date']), "%Y-%m-%d").date()
        except ValueError:
            results.append("Date Error")
            continue

        # 3. Look Forward 14 Days (2 Weeks)
        # For a 4-week hold, a 2-week post-exit window confirms if the trend died or paused.
        look_forward_date = exit_date + timedelta(days=14)
        
        if look_forward_date > today:
            days_left = (look_forward_date - today).days
            results.append(f"Wait {days_left}d")
            continue
            
        try:
            # Fetch data for that future window
            # We add 3 days to the end to account for weekends/holidays
            start = look_forward_date
            end = look_forward_date + timedelta(days=3)
            
            ticker = row['Ticker']
            # Fetch strictly 1 day of data
            data = yf.download(ticker, start=start, end=end, progress=False)
            
            # --- FIX MULTI-INDEX HEADERS (Same fix as backend.py) ---
            if isinstance(data.columns, pd.MultiIndex):
                try:
                    data = data['Adj Close']
                except KeyError:
                    data = data['Close']
            # -------------------------------------------------------

            if data.empty:
                results.append("Data Error")
                continue
                
            # Get the future price
            later_price = float(data.iloc[0])
            exit_price = float(row['Exit_Price'])
            direction = row['Direction'].upper()
            
            # Calculate "Money Left on Table"
            diff = 0.0
            if direction == "LONG":
                # If price is HIGHER 2 weeks later, you sold too early
                diff = round((later_price - exit_price) / exit_price * 100, 2)
            elif direction == "SHORT":
                # If price is LOWER 2 weeks later, you covered too early
                diff = round((exit_price - later_price) / exit_price * 100, 2)
            
            # Interpretation String
            if diff > 5.0:
                results.append(f"❌ Missed +{diff}%") # You missed big gains
            elif diff < -5.0:
                results.append(f"✅ Dodged {diff}%")   # You sold at the perfect time (price crashed after)
            else:
                results.append(f"⚪ Flat ({diff}%)")    # Price didn't move much
            
        except Exception as e:
            results.append("Error")
            
    return results

def get_macro_stats(df):
    """
    Calculates Win Rate based on Market Regime (No changes needed here)
    """
    if 'Market_Regime' not in df.columns:
        return {}
        
    stats = {}
    regimes = df['Market_Regime'].unique()
    
    for regime in regimes:
        subset = df[df['Market_Regime'] == regime]
        total_trades = len(subset)
        if total_trades == 0: continue
            
        wins = len(subset[subset['PnL_Percent'] > 0])
        win_rate = (wins / total_trades) * 100
        
        stats[regime] = {
            "Win Rate": f"{win_rate:.1f}%",
            "Trades": total_trades
        }
        
    return stats