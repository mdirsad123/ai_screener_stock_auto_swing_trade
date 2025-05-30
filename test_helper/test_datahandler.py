"""
python -m test_helper.test_datahandler
"""
import yfinance as yf
import pandas as pd
import numpy as np

def fetch_stock_data(symbol, period="6mo", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval)
        if df.empty:
            print(f"⚠️ Warning: No data for {symbol}")
            return None
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

# Example chart pattern detector
def detect_flag_pattern(df):
    recent = df['Close'].tail(10)
    if len(recent) < 5:
        return False, None
    returns = recent.pct_change().dropna()
    if returns.empty:
        return False, None
    std_dev = returns.std()
    if std_dev < 0.015:
        return True, 'Flag'
    return False, None

def analyze_stock(symbol):
    df = fetch_stock_data(symbol)
    if df is None:
        return []

    patterns = []
    for detector in [detect_flag_pattern]:  # add more detectors here
        try:
            found, pattern = detector(df)
            if found:
                patterns.append(pattern)
        except Exception as e:
            print(f"Error in detector for {symbol}: {e}")
    return patterns

# Run test
if __name__ == "__main__":
    stock = "TCS.NS"
    patterns = analyze_stock(stock)
    if patterns:
        print(f"✅ {stock} patterns found: {patterns}")
    else:
        print(f"❌ No patterns detected for {stock}")
