# Backtesting Smart Money Concept (SMC) Strategy with Liquidity Sweep + BOS + Order Block

"""
python -m forex_backtest.smc_backtest
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

curr_dir = os.path.dirname(__file__)
file_path = os.path.join(curr_dir, "GBPUSD_historical_data.csv")
data = pd.read_csv(file_path, parse_dates=['Date'])

# Rename columns to lowercase for strategy code
data.rename(columns={
    'Date': 'datetime',
    'Open': 'open',
    'High': 'high',
    'Low': 'low',
    'Close': 'close'
}, inplace=True)
data = data[['datetime', 'open', 'high', 'low', 'close']]
data.set_index('datetime', inplace=True)
data.sort_index(inplace=True)

# === Step 2: Define Utility Functions ===
def detect_liquidity_sweep(df):
    df['sweep_high'] = df['high'].shift(1) < df['high']
    df['sweep_low'] = df['low'].shift(1) > df['low']
    return df

def detect_bos(df):
    df['bos_up'] = (df['high'] > df['high'].shift(1)) & (df['low'] > df['low'].shift(1))
    df['bos_down'] = (df['low'] < df['low'].shift(1)) & (df['high'] < df['high'].shift(1))
    return df

def mark_order_block(df):
    df['bullish_ob'] = (df['close'].shift(1) < df['open'].shift(1)) & (df['close'] > df['open'])
    df['bearish_ob'] = (df['close'].shift(1) > df['open'].shift(1)) & (df['close'] < df['open'])
    return df

# === Step 3: Apply Smart Money Logic ===
data = detect_liquidity_sweep(data)
data = detect_bos(data)
data = mark_order_block(data)

# === Step 4: Define Trade Rules ===
trades = []
risk = 100  # per trade
rr_ratio = 2

for i in range(2, len(data)):
    if data.iloc[i-1].sweep_low and data.iloc[i].bos_up and data.iloc[i].bullish_ob:
        entry = data.iloc[i].close
        sl = data.iloc[i].low
        tp = entry + (entry - sl) * rr_ratio
        trades.append({
            'type': 'long',
            'entry': entry,
            'sl': sl,
            'tp': tp,
            'timestamp': data.index[i]
        })

    if data.iloc[i-1].sweep_high and data.iloc[i].bos_down and data.iloc[i].bearish_ob:
        entry = data.iloc[i].close
        sl = data.iloc[i].high
        tp = entry - (sl - entry) * rr_ratio
        trades.append({
            'type': 'long',
            'entry': entry,
            'sl': sl,
            'tp': tp,
            'timestamp': data.index[i]
        })

# === Step 5: Analyze Backtest Results ===
results = pd.DataFrame(trades)
results['pnl'] = 0

for i, row in results.iterrows():
    price_data = data.loc[row['timestamp']:].head(20)  # simulate next 20 candles
    hit_tp = price_data['high'].max() >= row['tp'] if row['type'] == 'long' else price_data['low'].min() <= row['tp']
    hit_sl = price_data['low'].min() <= row['sl'] if row['type'] == 'long' else price_data['high'].max() >= row['sl']

    if hit_tp and not hit_sl:
        results.at[i, 'pnl'] = risk * rr_ratio
    elif hit_sl:
        results.at[i, 'pnl'] = -risk

# === Step 6: Show Metrics ===
total_trades = len(results)

if total_trades == 0:
    print("No trades executed.")
    exit()

win_rate = len(results[results['pnl'] > 0]) / total_trades * 100
net_profit = results['pnl'].sum()

print("Total Trades:", total_trades)
print("Win Rate: {:.2f}%".format(win_rate))
print("Net Profit:", net_profit)

# Plot Equity Curve
results['equity'] = results['pnl'].cumsum()
results.set_index('timestamp')['equity'].plot(title="Equity Curve")
plt.show()

# === Step 2: Define Utility Functions ===
def detect_liquidity_sweep(df):
    df['sweep_high'] = df['high'].shift(1) < df['high']
    df['sweep_low'] = df['low'].shift(1) > df['low']
    return df

def detect_bos(df):
    df['bos_up'] = (df['high'] > df['high'].shift(1)) & (df['low'] > df['low'].shift(1))
    df['bos_down'] = (df['low'] < df['low'].shift(1)) & (df['high'] < df['high'].shift(1))
    return df

def mark_order_block(df):
    df['bullish_ob'] = (df['close'].shift(1) < df['open'].shift(1)) & (df['close'] > df['open'])
    df['bearish_ob'] = (df['close'].shift(1) > df['open'].shift(1)) & (df['close'] < df['open'])
    return df

# === Step 3: Apply Smart Money Logic ===
data = detect_liquidity_sweep(data)
data = detect_bos(data)
data = mark_order_block(data)

# === Step 4: Define Trade Rules ===
trades = []
risk = 100  # per trade
rr_ratio = 2

for i in range(2, len(data)):
    if data.iloc[i-1].sweep_low and data.iloc[i].bos_up and data.iloc[i].bullish_ob:
        entry = data.iloc[i].close
        sl = data.iloc[i].low
        tp = entry + (entry - sl) * rr_ratio
        trades.append({'type': 'long', 'entry': entry, 'sl': sl, 'tp': tp, 'timestamp': data.index[i]})

    if data.iloc[i-1].sweep_high and data.iloc[i].bos_down and data.iloc[i].bearish_ob:
        entry = data.iloc[i].close
        sl = data.iloc[i].high
        tp = entry - (sl - entry) * rr_ratio
        trades.append({'type': 'short', 'entry': entry, 'sl': sl, 'tp': tp, 'timestamp': data.index[i]})

# === Step 5: Analyze Backtest Results ===
results = pd.DataFrame(trades)
results['pnl'] = 0

for i, row in results.iterrows():
    price_data = data.loc[row['timestamp']:].head(20)  # simulate next 20 candles
    hit_tp = price_data['high'].max() >= row['tp'] if row['type'] == 'long' else price_data['low'].min() <= row['tp']
    hit_sl = price_data['low'].min() <= row['sl'] if row['type'] == 'long' else price_data['high'].max() >= row['sl']

    if hit_tp and not hit_sl:
        results.at[i, 'pnl'] = risk * rr_ratio
    elif hit_sl:
        results.at[i, 'pnl'] = -risk

# === Step 6: Show Metrics ===
total_trades = len(results)
win_rate = len(results[results['pnl'] > 0]) / total_trades * 100
net_profit = results['pnl'].sum()

print("Total Trades:", total_trades)
print("Win Rate: {:.2f}%".format(win_rate))
print("Net Profit:", net_profit)

# Plot Equity Curve
results['equity'] = results['pnl'].cumsum()
results.set_index('timestamp')['equity'].plot(title="Equity Curve")
plt.show()
