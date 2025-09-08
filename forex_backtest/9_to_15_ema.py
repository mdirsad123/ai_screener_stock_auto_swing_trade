"""
python -m forex_backtest.9_to_15_ema
"""
import yfinance as yf
import pandas as pd

def get_trend(symbol: str) -> str:
    # Fetch at least 60 days of 15-minute data to compute EMA200
    df = yf.download(symbol, period="60d", interval="15m", progress=False)

    if df.empty or len(df) < 200:
        raise ValueError("Not enough data to compute EMA 200")

    df.dropna(inplace=True)

    # Calculate EMAs
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_15'] = df['Close'].ewm(span=15, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # Get latest row
    latest = df.iloc[-1]

    ema_9 = latest['EMA_9']
    ema_15 = latest['EMA_15']
    ema_200 = latest['EMA_200']
    close = latest['Close']

    # Trend logic
    if ema_9 > ema_15 and close > ema_200:
        return "Uptrend"
    elif ema_9 < ema_15 and close < ema_200:
        return "Downtrend"
    else:
        return "Sideways or No clear trend"

# Example usage
if __name__ == "__main__":
    try:
        symbol = "IITL.NS"  # NSE example stock
        print(f"Fetching trend for {symbol}...")
        trend = get_trend(symbol)
        print(f"Trend for {symbol}: {trend}")
    except Exception as e:
        print(f"Error occurred: {e}")
