import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import ta
import numpy as np
import mplfinance as mpf
from ta.trend import IchimokuIndicator
from helpers.datahandler import *
from helpers.investing import *
from helpers.journal_handler import *
from helpers.intraday import *
from helpers.nse_data import *
from helpers.backtest import *
from helpers.FnO import analyse_option_chain, get_next_expiry_date
from helpers.online_brokers import KiteZerodha

# Page config
st.set_page_config(page_title="NSE Stock Scanner", layout="wide")

# Warning message
st.markdown("### <font color='red'>STOCK MARKET IS VERY RISKY UNTIL YOU DO IT PROPERLY. PLEASE DO NOT TAKE TRADES JUST BECAUSE THIS TOOL GIVES YOU THE NAME. APPLY YOUR OWN LEARNINGS, CREATE YOUR OWN STRATEGY, ASSESS RISK & TRADE THE PLAN.</font>", unsafe_allow_html=True)

# Initialize objects with error handling
try:
    In = Investing(check_fresh=False)  # Set to False initially to avoid data download
    Intra = IntraDay()
    NSE = NSEData()
    MS = MarketSentiment()
    BT = Backtest()
    ISS = IntradayStockSelection()
except Exception as e:
    st.error(f"Error initializing components: {str(e)}")
    st.stop()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Stock Analysis", "Swing Trading", "Intraday Trading", "Market Sentiment", "F&O Analysis", "Backtesting", "Risk Management"])

if page == "Stock Analysis":
    st.header("Stock Analysis")
    
    # Stock selection
    stock_symbol = st.text_input("Enter Stock Symbol (e.g., RELIANCE.NS)", "RELIANCE.NS")
    time_period = st.selectbox("Select Time Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"])
    
    if stock_symbol:
        try:
            # Fetch stock data
            stock = yf.Ticker(stock_symbol)
            hist = stock.history(period=time_period)
            
            if hist.empty:
                st.error(f"No data available for {stock_symbol}")
                st.stop()
            
            # Technical Analysis
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Technical Indicators")
                # RSI
                rsi_period = st.slider("RSI Period", 2, 30, 14)
                hist['RSI'] = ta.momentum.RSIIndicator(hist['Close'], window=rsi_period).rsi()
                
                # MACD
                macd_fast = st.slider("MACD Fast Period", 5, 20, 12)
                macd_slow = st.slider("MACD Slow Period", 15, 40, 26)
                macd_signal = st.slider("MACD Signal Period", 5, 15, 9)
                macd = ta.trend.MACD(hist['Close'], window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal)
                hist['MACD'] = macd.macd()
                hist['MACD_Signal'] = macd.macd_signal()
                hist['MACD_Hist'] = macd.macd_diff()
                
                # CCI
                cci_period = st.slider("CCI Period", 5, 30, 20)
                hist['CCI'] = ta.trend.CCIIndicator(hist['High'], hist['Low'], hist['Close'], window=cci_period).cci()
            
            with col2:
                st.subheader("Moving Averages")
                # Moving Averages
                hist['SMA_20'] = ta.trend.sma_indicator(hist['Close'], window=20)
                hist['SMA_50'] = ta.trend.sma_indicator(hist['Close'], window=50)
                hist['SMA_100'] = ta.trend.sma_indicator(hist['Close'], window=100)
                hist['SMA_200'] = ta.trend.sma_indicator(hist['Close'], window=200)
                
                # Ichimoku Cloud
                ichimoku = IchimokuIndicator(hist['High'], hist['Low'])
                hist['Ichimoku_A'] = ichimoku.ichimoku_a()
                hist['Ichimoku_B'] = ichimoku.ichimoku_b()
            
            # Display charts
            st.subheader("Price Chart with Indicators")
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=hist.index,
                                        open=hist['Open'],
                                        high=hist['High'],
                                        low=hist['Low'],
                                        close=hist['Close'],
                                        name='Price'))
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_20'], name='SMA 20', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], name='SMA 50', line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_100'], name='SMA 100', line=dict(color='green')))
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], name='SMA 200', line=dict(color='red')))
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            # Technical Analysis Signals
            st.subheader("Technical Analysis Signals")
            current_price = hist['Close'].iloc[-1]
            signals = {
                "RSI": "Oversold" if hist['RSI'].iloc[-1] < 30 else "Overbought" if hist['RSI'].iloc[-1] > 70 else "Neutral",
                "MACD": "Buy" if hist['MACD'].iloc[-1] > hist['MACD_Signal'].iloc[-1] else "Sell",
                "CCI": "Oversold" if hist['CCI'].iloc[-1] < -100 else "Overbought" if hist['CCI'].iloc[-1] > 100 else "Neutral",
                "SMA_20": "Above" if current_price > hist['SMA_20'].iloc[-1] else "Below",
                "SMA_50": "Above" if current_price > hist['SMA_50'].iloc[-1] else "Below",
                "SMA_100": "Above" if current_price > hist['SMA_100'].iloc[-1] else "Below",
                "SMA_200": "Above" if current_price > hist['SMA_200'].iloc[-1] else "Below"
            }
            st.table(pd.DataFrame(list(signals.items()), columns=['Indicator', 'Signal']))
            
        except Exception as e:
            st.error(f"Error analyzing stock: {str(e)}")

elif page == "Swing Trading":
    st.header("Swing Trading Strategies")
    
    strategy = st.selectbox("Select Strategy", ["Breakout", "44-SMA", "Golden Crossover", "RSI Signal", "MACD Signal", "CCI Signal"])
    
    if strategy == "Breakout":
        st.subheader("Breakout Stocks")
        diff = st.slider("Price Difference %", 0.1, 2.0, 0.7)
        min_count = st.slider("Minimum Touches", 3, 10, 5)
        lookback = st.slider("Lookback Period", 5, 20, 10)
        
        if st.button("Find Breakout Stocks"):
            stocks = In.tight_consolidation_stocks(stocks='nifty_500', diff=diff/100, min_count=min_count, lookback_period=lookback)
            st.dataframe(stocks)
    
    elif strategy == "44-SMA":
        st.subheader("44-SMA Strategy")
        budget = st.number_input("Total Budget", value=40000)
        risk = st.number_input("Risk per Trade", value=400)
        diff = st.number_input("Price Difference", value=150)
        
        if st.button("Find 44-SMA Stocks"):
            df = In.show_full_stats(budget=budget, risk=risk, diff=diff, nifty='nifty_50')
            st.dataframe(df[(df['RSI Value'] < 80) & (df['CCI Value'] < 250)])

elif page == "Intraday Trading":
    st.header("Intraday Trading Strategies")
    
    strategy = st.selectbox("Select Intraday Strategy", ["Pivot Points", "Narrow Range", "Whole Number Open", "ATR"])
    
    if strategy == "Pivot Points":
        st.subheader("Pivot Points Analysis")
        symbol = st.text_input("Enter Stock Symbol", "BSOFT")
        days_back = st.slider("Days Back", 1, 10, 5)
        
        if st.button("Calculate Pivot Points"):
            data = In.open_live_stock_data(symbol)
            pivot_data = In.get_Pivot_Points(data, plot=True, num_days_back=days_back)
            st.dataframe(pivot_data)
    
    elif strategy == "Narrow Range":
        st.subheader("Narrow Range Strategy")
        range_days = st.slider("Range Days", 10, 30, 20)
        
        if st.button("Find Narrow Range Stocks"):
            for name in In.data['nifty_500']:
                if Intra.NR_strategy(name, range_=range_days):
                    st.write(f"{name}: {Intra.prob_by_percent_change(symbol=[name], index=None, time_period=10, change_percent=0.07)}")

elif page == "Market Sentiment":
    st.header("Market Sentiment Analysis")
    
    if st.button("Get Market Sentiment"):
        sentiment = MS.get_live_sentiment()
        st.write(sentiment)
    
    st.subheader("VIX Analysis")
    if st.button("Get VIX"):
        vix = NSE.get_VIX()
        st.write(vix)
    
    st.subheader("52 Week High/Low Stocks")
    direction = st.radio("Select Direction", ["High", "Low"])
    if st.button("Get 52W Stocks"):
        stocks = NSE.stocks_at_52W(direction=direction.lower())
        st.dataframe(stocks)

elif page == "F&O Analysis":
    st.header("Futures and Options Analysis")
    
    symbol = st.text_input("Enter Stock Symbol for Option Chain", "TATACHEM")
    if st.button("Analyze Option Chain"):
        filtered_df = analyse_option_chain(symbol, plot=True, fig_size=(21, 6.7))
        st.dataframe(filtered_df)

elif page == "Backtesting":
    st.header("Strategy Backtesting")
    
    strategy = st.selectbox("Select Strategy to Backtest", ["CCI", "MA", "RSI", "MACD", "Stochastic Oscillator"])
    
    if strategy == "CCI":
        st.subheader("CCI Backtesting")
        buying_thresh = st.number_input("Buying Threshold", value=-100)
        selling_thresh = st.number_input("Selling Threshold", value=100)
        window = st.number_input("Window", value=20)
        
        if st.button("Run CCI Backtest"):
            cci_parameters = {
                'buying_thresh': buying_thresh,
                'selling_thresh': selling_thresh,
                'window': window,
                'cols': ('OPEN', 'CLOSE', 'LOW', 'HIGH', 'DATE')
            }
            results = BT.backtest('cci', min_days=365, top_n=10, stocks='nifty_500', **cci_parameters)
            st.dataframe(results)

elif page == "Risk Management":
    st.header("Risk Management")
    
    symbol = st.text_input("Enter Stock Symbol", "NIITLTD")
    budget = st.number_input("Total Budget", value=40000)
    risk = st.number_input("Risk per Trade", value=400)
    
    if st.button("Calculate Position Size"):
        particulars = In.get_particulars(symbol, budget=budget, risk=risk)
        st.write(particulars) 