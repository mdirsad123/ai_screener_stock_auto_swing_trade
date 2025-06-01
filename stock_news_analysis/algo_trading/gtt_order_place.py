"""
python -m stock_news_analysis.algo_trading.gtt_order_place
"""

import json
import requests
import pandas as pd
from datetime import datetime, time

# Load instruments from JSON
with open("upstox_instruments_nse.json", "r") as f:
    instruments_df = pd.DataFrame(json.load(f))

# Load token
with open("upstox_token.json") as f:
    access_token = json.load(f)["access_token"]

# Headers
auth_headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {access_token}"
}

def is_order_time():
    """Check if current time is within Upstox GTT allowed window (9:00 AM to 6:00 PM IST)."""
    now = datetime.now().time()
    return time(9, 0) <= now <= time(18, 0)

def get_instrument_token(symbol, exchange="NSE"):
    match = instruments_df[
        (instruments_df['trading_symbol'].str.upper() == symbol.upper()) &
        (instruments_df['exchange'].str.upper() == exchange.upper())
    ]
    if not match.empty:
        return match.iloc[0]['instrument_key']
    else:
        raise ValueError(f"❌ Instrument for symbol '{symbol}' not found.")

def get_ltp(symbol, exchange="NSE"):
    try:
        instrument_token = get_instrument_token(symbol, exchange)  # e.g., "NSE_EQ|INE848E01016"
        url = f"https://api.upstox.com/v2/market-quote/ohlc?instrument_key={instrument_token}"

        response = requests.get(url, headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and instrument_token in data['data']:
                return data['data'][instrument_token]['last_price']
            else:
                raise Exception(f"⚠️ Instrument data not found in response: {data}")
        else:
            raise Exception(f"❌ Failed to fetch LTP: {response.status_code} {response.text}")
    except Exception as e:
        print(str(e))
        return None

def place_gtt_order_by_symbol(symbol, entry_price, target_price, stoploss_price, quantity=1,
                               transaction_type="BUY", exchange="NSE", product="D"):
    if not is_order_time():
        print("⚠️ GTT orders can only be placed between 9:00 AM and 6:00 PM IST.")
        return

    try:
        instrument_token = get_instrument_token(symbol, exchange)
        print(f"🔑 Instrument token for {symbol}: {instrument_token}")
    except Exception as e:
        print("❌ Error fetching instrument token:", e)
        return

    url = "https://api.upstox.com/v3/order/gtt/place"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "type": "MULTIPLE",
        "quantity": quantity,
        "product": product,
        "instrument_token": instrument_token,
        "transaction_type": transaction_type.upper(),
        "rules": [
            {
                "strategy": "ENTRY",
                "trigger_type": "BELOW",
                "trigger_price": entry_price
            },
            {
                "strategy": "TARGET",
                "trigger_type": "IMMEDIATE",
                "trigger_price": target_price
            },
            {
                "strategy": "STOPLOSS",
                "trigger_type": "IMMEDIATE",
                "trigger_price": stoploss_price
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print("✅ GTT order placed successfully!")
        print(response.json())
    else:
        print("❌ Failed to place GTT order")
        print(response.status_code, response.text)

def place_gtt_order_by_symbol_percent(symbol, target_percent, stoploss_percent, entry_price=None,
                                      quantity=1, transaction_type="BUY", exchange="NSE", product="D"):
    try:
        if entry_price is None:
            entry_price = get_ltp(symbol, exchange)
            print(f"📈 Using market LTP for {symbol}: ₹{entry_price}")
        target_price = round(entry_price * (1 + target_percent / 100), 2)
        stoploss_price = round(entry_price * (1 - stoploss_percent / 100), 2)

        print(f"🧠 Entry: ₹{entry_price}, Target (+{target_percent}%): ₹{target_price}, Stop Loss (-{stoploss_percent}%): ₹{stoploss_price}")
        place_gtt_order_by_symbol(symbol, entry_price, target_price, stoploss_price,
                                  quantity, transaction_type, exchange, product)

    except Exception as e:
        print("❌ Error placing order by percentage:", e)


# ========== EXAMPLE USAGE ==========

if __name__ == "__main__":
    # Place fixed price GTT order
    place_gtt_order_by_symbol(
        symbol="IDEA",
        entry_price=2.57,
        target_price=2.60,
        stoploss_price=2.55,
        quantity=1
    )

    # Place GTT order using percentage target and stoploss
    # place_gtt_order_by_symbol_percent(
    #     symbol="IDEA",
    #     target_percent=10,
    #     stoploss_percent=3,
    #     quantity=1
    # )
    # entry_price = get_ltp(symbol="IDEA", exchange="NSE")
    # print(f"📈 Current LTP for IDEA: ₹{entry_price}")
    # instrument_token = get_instrument_token(symbol="IDEA", exchange="NSE")
    # print(f"🔑 Instrument token for IDEA: {instrument_token}")
