"""
python -m investing_risk_management.risk_management
"""

import yfinance as yf
import warnings
import pandas as pd
import numpy as np

def get_live_risk_config(
    symbol: str,
    budget: float,
    risk_per_trade: float,
    risk_to_reward_ratio: float = 2,
    leverage: float = 1,
    delta: float = 0.001,
    stop_loss_manual: float = None,
    entry_manual: float = None,
    plot: bool = False
) -> dict:
    budget *= leverage
    df = yf.download(symbol, period="5d", interval="1d")
    if df.empty:
        return {"error": f"Could not fetch data for {symbol}"}

    latest = df.iloc[-1]

    try:
        high = float(latest["High"])
        low = float(latest["Low"])
        close = float(latest["Close"])
    except (TypeError, ValueError):
        return {"error": f"Invalid data format for {symbol}"}

    # Entry and Stop Loss logic
    buy_price = entry_manual or round(high + (high * delta), 2)
    stop_loss = stop_loss_manual or round(low - (low * delta), 2)
    diff = round(buy_price - stop_loss, 2)

    if diff <= 0:
        return {"error": f"Invalid stop-loss for {symbol}"}

    # Calculate quantity
    quantity = int(min(risk_per_trade // diff, budget // buy_price))
    if quantity < 1:
        return {
            "error": f"Risk too low or stock too expensive. Increase budget or risk_per_trade."
        }

    # Profit and Target
    profit = round(risk_to_reward_ratio * diff, 2)
    target = round(buy_price + profit, 2)
    investment = round(quantity * buy_price, 2)

    # R:R ratio (shown as 1:X)
    try:
        rr_ratio = profit / diff
        rr_text = f"1:{int(rr_ratio)}" if rr_ratio.is_integer() else f"1:{round(rr_ratio, 2)}"
    except (ZeroDivisionError, TypeError):
        rr_text = "N/A"

    # Optional plotting
    if plot:
        try:
            import mplfinance as mpf
            df_plot = df.tail(20).copy()
            df_plot = df_plot.astype(float)
            df_plot.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
            if not df_plot.empty:
                mpf.plot(df_plot, type='candle', title=f"{symbol} - Candlestick")
        except ImportError:
            print("mplfinance not installed.")
        except Exception as e:
            print(f"Plotting failed: {e}")

    return {
        "Symbol": symbol,
        "Buy Price": buy_price,
        "Stop Loss": stop_loss,
        "Target Price": target,
        "Risk/Share": diff,
        "Profit/Share": profit,
        "Stop Loss %": round((diff / buy_price) * 100, 2),
        "Profit %": round((profit / buy_price) * 100, 2),
        "Quantity": quantity,
        "Investment": investment,
        "Total Risk": round(quantity * diff, 2),
        "Total Profit": round(quantity * profit, 2),
        "RR Ratio": rr_text  # ✅ Added for better user display
    }

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    symbol = "RELIANCE.NS"
    budget = 100000  # Example budget
    risk_per_trade = 1000  # Example risk per trade

    result = get_live_risk_config(symbol, budget, risk_per_trade, plot=True)
    print(pd.DataFrame([result]))