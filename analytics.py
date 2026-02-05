import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def get_paper_hands_score(df):
    """
    Checks if you sold too early.
    Returns: A DataFrame with a new column 'Missed_Gains'
    """
    print("Running Paper Hands Analysis...")
    results = []
    
    # We only look at trades that are at least 5 days old
    today = datetime.now().date()
    
    for index, row in df.iterrows():
        # skip if already analyzed or no exit price
        if row['Exit_Price'] == 0: continue
            
        trade_date = datetime.strptime(row['Date'], "%Y-%m-%d").date()
        look_forward_date = trade_date + timedelta(days=5)
        
        # Can't analyze future dates
        if look_forward_date > today:
            results.append("Pending (Wait 5 days)")
            continue
            
        # Optimization: Don't re-fetch if we ran this before (you'd need a database for this, 
        # but for now we fetch live to keep it simple)
        
        try:
            # Fetch data for the specific "5 days later" window
            start = look_forward_date
            end = look_forward_date + timedelta(days=3) # Buffer for weekends
            
            ticker = row['Ticker']
            data = yf.download(ticker, start=start, end=end, progress=False)
            
            # Handle MultiIndex headers (The Fix from before)
            if isinstance(data.columns, pd.MultiIndex):
                try:
                    data = data['Adj Close']
                except KeyError:
                    data = data['Close']
            
            if data.empty:
                results.append("Data Error")
                continue
                
            # Get the price 5 days later
            later_price = float(data.iloc[0])
            exit_price = float(row['Exit_Price'])
            direction = row['Direction'].lower()
            
            # Calculate "Money Left on Table"
            if direction == "long":
                # If price went UP after you sold, you missed out (Negative feeling)
                diff = round((later_price - exit_price) / exit_price * 100, 2)
            else:
                # If short, and price went DOWN, you covered too early
                diff = round((exit_price - later_price) / exit_price * 100, 2)
            
            results.append(f"{diff}%")
            
        except Exception as e:
            results.append("Error")
            
    return results

def get_macro_stats(df):
    """
    Calculates Win Rate based on Market Regime (Bullish vs Bearish)
    """
    if 'Market_Regime' not in df.columns:
        return None
        
    stats = {}
    
    # Group by Regime
    regimes = df['Market_Regime'].unique()
    
    for regime in regimes:
        # Filter for this regime
        subset = df[df['Market_Regime'] == regime]
        total_trades = len(subset)
        
        # Count Wins (PnL > 0)
        wins = len(subset[subset['PnL_Percent'] > 0])
        win_rate = (wins / total_trades) * 100
        
        stats[regime] = {
            "Win Rate": f"{win_rate:.1f}%",
            "Trades": total_trades
        }
        
    return stats