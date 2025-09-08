
"""
python -m forex_backtest.forex
"""
import pandas as pd
import numpy as np
import ta
import os

# Load data
file_path = os.path.join(os.path.dirname(__file__), 'AUDJPY_historical_data.csv')
df = pd.read_csv(file_path, header=0, skip_blank_lines=True)
df.columns = [col.strip() for col in df.columns]

# Parse datetime
df['datetime'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=False)
df.dropna(subset=['datetime'], inplace=True)
df = df.sort_values(by='datetime').copy()

# Keep OHLC only
df = df[['datetime', 'Open', 'High', 'Low', 'Close']]
df.set_index('datetime', inplace=True)

# Remove duplicate timestamps (critical)
df = df[~df.index.duplicated(keep='first')]

# Convert columns to float
df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].astype(float)

# Indicators
df['EMA18'] = ta.trend.ema_indicator(df['Close'], window=18)
df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50)
df['SMA200'] = ta.trend.sma_indicator(df['Close'], window=200)

# Bullish Engulfing (relaxed)
def is_bullish_engulfing(prev, curr):
    return (
        prev['Close'] < prev['Open'] and
        curr['Close'] > curr['Open'] and
        curr['Close'] > prev['Close'] and
        curr['Open'] < prev['Open']
    )

df['bullish_engulfing'] = False
for i in range(1, len(df)):
    df.iloc[i, df.columns.get_loc('bullish_engulfing')] = is_bullish_engulfing(df.iloc[i-1], df.iloc[i])

# Swing low detection: local minima in Low
df['swing_low'] = df['Low'][(df['Low'].shift(1) > df['Low']) & (df['Low'].shift(-1) > df['Low'])]

# Backtest
trades = []
spread = 1  # pip
min_risk_pips = 8  # minimum 1R = 8 pips

for i in range(2, len(df)):
    row = df.iloc[i]

    # Uptrend condition
    if row['EMA18'] > row['EMA50'] > row['SMA200']:
        # Bullish Engulfing condition
        if df.iloc[i]['bullish_engulfing']:
            # Support test: price near EMA18 or EMA50
            near_ema = abs(row['Low'] - row['EMA18']) < 0.0005 or abs(row['Low'] - row['EMA50']) < 0.0005
            if not near_ema:
                continue

            entry_price = row['High'] + spread * 0.0001
            stop_loss = row['Low'] - spread * 0.0001
            one_r = entry_price - stop_loss

            if one_r < 0.0008:  # Less than 8 pips
                continue

            target_price = entry_price + 2 * one_r

            entry_time = df.index[i]
            exit_time = None
            hit_tp = False
            hit_sl = False

            for j in range(i+1, min(i+21, len(df))):  # check next 20 candles
                future = df.iloc[j]
                if future['Low'] <= stop_loss:
                    exit_price = stop_loss
                    exit_time = df.index[j]
                    hit_sl = True
                    break
                elif future['High'] >= target_price:
                    exit_price = target_price
                    exit_time = df.index[j]
                    hit_tp = True
                    break

            trades.append({
                'Entry Time': entry_time,
                'Entry Price': round(entry_price, 5),
                'Stop Loss': round(stop_loss, 5),
                'Target Price': round(target_price, 5),
                'Exit Time': exit_time,
                'Exit Price': round(exit_price, 5) if exit_time else None,
                'Result': 'TP' if hit_tp else ('SL' if hit_sl else 'Open')
            })

# Results
results = pd.DataFrame(trades)
if results.empty:
    print("No trades were triggered. Check if EMA/SMA formed correctly or relax your filters.")
    exit()

total_trades = len(results)
wins = len(results[results['Result'] == 'TP'])
losses = len(results[results['Result'] == 'SL'])
win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

print(f"Total Trades: {total_trades}")
print(f"Wins: {wins}")
print(f"Losses: {losses}")
print(f"Win Rate: {win_rate:.2f}%")

# Export
results.to_csv('tce_backtest_results.csv', index=False)
print("Results saved to tce_backtest_results.csv")
