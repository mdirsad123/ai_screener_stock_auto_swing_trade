"""
python screener_folder/pattern_detection.py
"""

import pandas as pd
from datetime import timedelta, date
import os
import re
from nsepy import get_history

# --- Clean up raw company name into valid NSE symbol ---
def clean_symbol(raw_symbol):
    raw_symbol = str(raw_symbol).upper()
    raw_symbol = re.sub(r'[^\w]', '', raw_symbol)  # Remove special characters
    words = raw_symbol.split()
    if len(words) > 1:
        raw_symbol = words[0]
    return raw_symbol

# --- Detect candlestick patterns ---
def detect_patterns(df_ohlc, symbol):
    last_15 = df_ohlc.tail(15)

    for i in range(1, len(last_15)):
        prev = last_15.iloc[i - 1]
        curr = last_15.iloc[i]
        date_str = curr.name.strftime('%d-%m-%Y')

        # Bullish Engulfing
        if (prev['Close'] < prev['Open'] and
            curr['Close'] > curr['Open'] and
            curr['Open'] < prev['Close'] and
            curr['Close'] > prev['Open']):
            pattern_results.append({"symbol": symbol, "pattern_name": "Bullish Engulfing", "date_detected": date_str})

        # Hammer
        body = abs(curr['Close'] - curr['Open'])
        lower_shadow = curr['Open'] - curr['Low'] if curr['Close'] > curr['Open'] else curr['Close'] - curr['Low']
        upper_shadow = curr['High'] - max(curr['Open'], curr['Close'])
        if lower_shadow > 2 * body and upper_shadow < body:
            pattern_results.append({"symbol": symbol, "pattern_name": "Hammer", "date_detected": date_str})

        # Marubozu
        if abs(curr['Open'] - curr['Low']) < 0.2 and abs(curr['High'] - curr['Close']) < 0.2:
            pattern_results.append({"symbol": symbol, "pattern_name": "Marubozu", "date_detected": date_str})

        # Doji
        if abs(curr['Close'] - curr['Open']) < (0.1 * (curr['High'] - curr['Low'])):
            pattern_results.append({"symbol": symbol, "pattern_name": "Doji", "date_detected": date_str})


# --- Input and Output Paths ---
input_csv = r"D:\Stock_market\NSE-Stock-Scanner\output\screener_top_gainers.csv"
output_csv = r"D:\Stock_market\NSE-Stock-Scanner\output\pattern_detected.csv"

# Read top gainers list
df = pd.read_csv(input_csv)
symbols = df['Symbol'].unique()

# Store results
pattern_results = []

# Loop through each symbol and detect patterns
for symbol in symbols:
    try:
        cleaned_symbol = clean_symbol(symbol)
        df_hist = get_history(
            symbol=cleaned_symbol,
            start=date.today() - timedelta(days=30),
            end=date.today()
        )
        if not df_hist.empty:
            detect_patterns(df_hist, cleaned_symbol)
        else:
            print(f"⚠️ No data for: {cleaned_symbol}")
    except Exception as e:
        print(f"❌ Failed to get data for {symbol} → {e}")

# Save results to CSV
df_result = pd.DataFrame(pattern_results)
os.makedirs(os.path.dirname(output_csv), exist_ok=True)
df_result.to_csv(output_csv, index=False)
print(f"✅ Pattern detection complete. Results saved to: {output_csv}")
