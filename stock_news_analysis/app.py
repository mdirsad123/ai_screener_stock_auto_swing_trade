"""
streamlit run stock_news_analysis/app.py
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import subprocess
import threading
import schedule
from streamlit_autorefresh import st_autorefresh
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import seaborn as sns
import matplotlib.pyplot as plt
from analysis.read_latest_csv import load_latest_data_output_sentiment
from analysis.read_latest_csv import load_latest_data_output_chart_ind

# Set page config
st.set_page_config(
    page_title="Stock News Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

def run_screener():
    """Run the daily screener script"""
    try:
        venv_python = r"D:\Stock_market\NSE-Stock-Scanner\.venv\Scripts\python.exe"
        subprocess.run([venv_python, "-m", "stock_news_analysis.main"], check=True)
        return True
    except Exception as e:
        st.error(f"Error running screener: {e}")
        return False

def schedule_screener():
    """Schedule the screener to run every 10 minutes"""
    while True:
        schedule.run_pending()
        time.sleep(1)

def create_sentiment_chart(df):
    """Create an interactive sentiment distribution chart"""
    if df is None or df.empty or 'overall_sentiment' not in df.columns:
        return go.Figure()

    sentiment_counts = df['overall_sentiment'].value_counts().reset_index()
    sentiment_counts.columns = ['Sentiment', 'Count']
    
    color_map = {
        'Very Positive': '#00ff00',
        'Positive': '#90EE90',
        'Neutral': '#FFD700',
        'Negative': '#FFB6C1',
        'Very Negative': '#FF0000',
        'No Text': '#D3D3D3'
    }
    
    fig = px.bar(
        sentiment_counts,
        x='Sentiment',
        y='Count',
        color='Sentiment',
        color_discrete_map=color_map,
        title="Sentiment Distribution"
    )
    
    fig.update_layout(
        xaxis_title="Sentiment",
        yaxis_title="Count",
        showlegend=False,
        height=400
    )
    return fig

def create_confidence_chart(df):
    """Create a confidence score distribution chart"""
    if df is None or 'confidence' not in df.columns or df['confidence'].isnull().all():
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Box(
        y=df['confidence'],
        name='Confidence Scores',
        boxpoints='all',
        jitter=0.3,
        pointpos=-1.8
    ))
    fig.update_layout(
        title="Confidence Score Distribution",
        yaxis_title="Confidence Score",
        height=400
    )
    return fig

def process_sentiment(df):
    """Use existing sentiment columns instead of recomputing"""
    if df is None or df.empty:
        return None

    df_processed = df.copy()
    
    # Use final_sentiment and confidence columns from existing data
    df_processed['overall_sentiment'] = df_processed.get('final_sentiment', 'No Text')
    df_processed['confidence'] = df_processed.get('confidence', 0)
    df_processed['Time'] = df_processed.get('Time', 0)

    # Optional: If you want to show all sentiment scores together
    df_processed['sentiment_metrics'] = df_processed.apply(lambda row: {
        'vader_score': row.get('vader_score'),
        'textblob_score': row.get('textblob_score'),
        'bert_sentiment': row.get('bert_sentiment'),
        'confidence': row.get('confidence')
    }, axis=1)

    return df_processed

def main():
    st.title("📈 Stock News Analysis Dashboard")
    
    # Sidebar controls
    st.sidebar.header("Controls")
    auto_refresh = st.sidebar.checkbox("Auto-refresh dashboard every 5 minutes", value=True)
    auto_screener = st.sidebar.checkbox("Run screener every 10 minutes", value=False)

    # Session state
    if 'last_data' not in st.session_state:
        st.session_state.last_data = None
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None
    if 'scheduler_running' not in st.session_state:
        st.session_state.scheduler_running = False
    if 'next_run_time' not in st.session_state:
        st.session_state.next_run_time = None

    if auto_screener:
    # Refresh every second to keep countdown live
        st_autorefresh(interval=1000, key="screener_timer_refresh", limit=1000000)
        
    # Screener scheduling logic (always check the current checkbox value)
    if auto_screener and not st.session_state.scheduler_running:
        def run_screener_with_timer():
            run_screener()
            st.session_state.next_run_time = datetime.now() + timedelta(minutes=2)

        st.session_state.next_run_time = datetime.now() + timedelta(minutes=2)
        schedule.every(10).minutes.do(run_screener_with_timer)

        scheduler_thread = threading.Thread(target=schedule_screener, daemon=True)
        scheduler_thread.start()

        st.session_state.scheduler_running = True
        st.sidebar.success("Screener scheduled to run every 10 minutes")

    elif not auto_screener and st.session_state.scheduler_running:
        schedule.clear()
        st.session_state.scheduler_running = False
        st.session_state.next_run_time = None
        st.sidebar.info("Screener scheduling stopped")

    # Show countdown timer
    # if st.session_state.scheduler_running and st.session_state.next_run_time:
    #     time_left = st.session_state.next_run_time - datetime.now()
    #     minutes, seconds = divmod(int(time_left.total_seconds()), 60)
    #     if minutes >= 0 and seconds >= 0:
    #         st.sidebar.markdown(f"⏳ **Next screener run in:** {minutes:02d}:{seconds:02d} minutes")

    # Optional: Auto-refresh the app
    if auto_refresh:
        st_autorefresh(interval=5 * 60 * 1000, key="auto_refresh")  # 5 minutes


   
 # ---------------------------------------------------------------
    df_sentiment_data = load_latest_data_output_sentiment()
    df_chart_ind_data = load_latest_data_output_chart_ind()
    view = st.sidebar.radio("Select View", ["Sentiment", "Chart Patterns", "Technical Indicators", "Smart Trade Signals"])

    if view == "Sentiment":
    # show sentiment charts and tables
        total_announcements = len(df_sentiment_data) if df_sentiment_data is not None else 0
        st.subheader(f'Total {total_announcements} Latest Announcements')
        if df_sentiment_data is not None:
            df_processed = process_sentiment(df_sentiment_data)
            st.session_state.last_data = df_processed
            st.session_state.last_update = datetime.now()
            st.dataframe(
                df_processed[['Company', 'Headline', 'Time', 'overall_sentiment', 'confidence']],
                use_container_width=True
            )
        else:
            st.warning("No data available. Please run the screener first.")



        # sentiment statistics
        if st.session_state.last_data is not None:
            
            sentiment_counts = st.session_state.last_data['overall_sentiment'].value_counts()
            total = len(st.session_state.last_data)
            st.subheader("Sentiment Statistics")
            ordered_sentiments = ["Very Positive", "Positive", "Neutral", "Negative", "Very Negative"]
            # Filter only the sentiments that are present
            filtered_sentiments = [(s, sentiment_counts[s]) for s in ordered_sentiments if s in sentiment_counts]
            # Create columns dynamically
            cols = st.columns(len(filtered_sentiments))
            # Display metrics row-wise
            for col, (sentiment, count) in zip(cols, filtered_sentiments):
                percentage = (count / total) * 100
                col.metric(sentiment, f"{percentage:.1f}%", f"{count} announcements")

        # --- New Section: Sentiment-Based Tables ---

        st.header("📊 Sentiment-Based Stock Breakdown")

        # Define the sentiment categories in desired order
        categories = ["Very Positive", "Positive", "Neutral", "Negative", "Very Negative"]

        for sentiment in categories:
            df_s = df_sentiment_data[df_sentiment_data['final_sentiment'] == sentiment]
            if not df_s.empty:
                df_s = df_s[['Company', 'Headline', 'Time', 'confidence']].copy()
                df_s = df_s.sort_values('confidence', ascending=False)
                df_s['confidence'] = df_s['confidence'].apply(lambda x: f"{x:.1%}")  # format as percentage

                st.subheader(
                    f"🟢 {sentiment}" if "Positive" in sentiment
                    else f"🔴 {sentiment}" if "Negative" in sentiment
                    else f"⚪ {sentiment}"
                )

                st.dataframe(
                    df_s,
                    use_container_width=True,
                    column_config={
                        "Company": st.column_config.Column(width="small"),
                        "Headline": st.column_config.Column(width="large"),
                        "Time": st.column_config.Column(width="medium"),
                        "confidence": st.column_config.Column(width="small")
                    }
                )
    # ------------------------------------------------------------------------------------------

        # Count of Sentiments Pie Chart
        color_map = {
            'Very Positive': '#00ff00',
            'Positive': '#90EE90',
            'Neutral': '#FFD700',
            'Negative': '#FFB6C1',
            'Very Negative': '#FF0000',
            'No Text': '#D3D3D3'
        }

        # Count sentiments
        sentiment_counts = df_sentiment_data['final_sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Count']

        # Create pie chart with custom color map
        fig_pie = px.pie(
            sentiment_counts,
            values='Count',
            names='Sentiment',
            title='Sentiment Distribution',
            hole=0.4,
            color='Sentiment',
            color_discrete_map=color_map
        )

        # Display in Streamlit
        st.plotly_chart(fig_pie, use_container_width=True)

    # ------------------------------------------------------------------------------------------

        # Bar Chart: Top Companies by Positive News
        positive_df = df_sentiment_data[df_sentiment_data['final_sentiment'].isin(['Very Positive', 'Positive'])]
        top_companies = positive_df['Company'].value_counts().nlargest(10).reset_index()
        top_companies.columns = ['Company', 'Positive News Count']
        fig_bar = px.bar(top_companies, x='Company', y='Positive News Count',
                        title='Top Companies with Most Positive News')
        st.plotly_chart(fig_bar, use_container_width=True)
        
# ---------------------------------------------------------------------------------------------------------
    
    elif view == "Chart Patterns":
        df_chart = df_chart_ind_data[['Company', 'Chart_Pattern']].dropna()
        df_chart = df_chart.assign(Patterns=df_chart['Chart_Pattern'].str.split(', ')).explode('Patterns')
        st.dataframe(df_chart)

        pattern_counts = df_chart['Patterns'].value_counts().reset_index()
        pattern_counts.columns = ['Chart Pattern', 'Frequency']
        st.bar_chart(pattern_counts.set_index('Chart Pattern'))

        fig = px.pie(pattern_counts, values='Frequency', names='Chart Pattern', title='Chart Pattern Distribution')
        st.plotly_chart(fig)

        selected_pattern = st.selectbox("Select a Chart Pattern", df_chart['Patterns'].unique())
        filtered_df = df_chart[df_chart['Patterns'] == selected_pattern]
        st.write(f"Companies with {selected_pattern} pattern:")
        st.dataframe(filtered_df)

        df_combo = df_chart_ind_data[['Chart_Pattern', 'final_sentiment']].dropna()
        df_combo = df_combo.assign(Patterns=df_combo['Chart_Pattern'].str.split(', ')).explode('Patterns')
        pattern_sentiment = df_combo.groupby(['Patterns', 'final_sentiment']).size().unstack(fill_value=0)
        st.dataframe(pattern_sentiment)

        
        fig, ax = plt.subplots()
        sns.heatmap(pattern_sentiment, annot=True, fmt='d', cmap='Blues', ax=ax)
        st.pyplot(fig)

        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Filtered Data", csv, "filtered_chart_pattern.csv", "text/csv")




# ---------------------------------------------------------------------------------------------------------

    elif view == "Technical Indicators":
        st.subheader("Technical Indicators Analysis")

        # Preprocess data
        df_ind = df_chart_ind_data[['Company', 'Tech_Indicator']].dropna()
        df_ind = df_ind.assign(Indicators=df_ind['Tech_Indicator'].str.split(', ')).explode('Indicators')

        # Show raw data
        st.dataframe(df_ind)

        # Indicator frequency analysis
        st.markdown("### 📊 Frequency of Technical Indicators")
        ind_counts = df_ind['Indicators'].value_counts().reset_index()
        ind_counts.columns = ['Technical Indicator', 'Frequency']
        st.bar_chart(ind_counts.set_index('Technical Indicator'))

        # Pie chart of indicators
        st.markdown("### 🥧 Indicator Distribution")
        fig = px.pie(ind_counts, values='Frequency', names='Technical Indicator', title='Technical Indicator Distribution')
        st.plotly_chart(fig)

        # Filter by selected indicator
        st.markdown("### 🔍 Filter by Technical Indicator")
        selected_ind = st.selectbox("Select an Indicator", df_ind['Indicators'].unique())
        filtered_ind_df = df_ind[df_ind['Indicators'] == selected_ind]
        st.write(f"Companies with `{selected_ind}` indicator:")
        st.dataframe(filtered_ind_df)

        # Correlation with final sentiment
        st.markdown("### 🔗 Correlation with Sentiment")
        df_ind_sent = df_chart_ind_data[['Tech_Indicator', 'final_sentiment']].dropna()
        df_ind_sent = df_ind_sent.assign(Indicators=df_ind_sent['Tech_Indicator'].str.split(', ')).explode('Indicators')
        ind_sentiment = df_ind_sent.groupby(['Indicators', 'final_sentiment']).size().unstack(fill_value=0)

        fig2, ax = plt.subplots()
        sns.heatmap(ind_sentiment, annot=True, fmt='d', cmap='Greens', ax=ax)
        st.pyplot(fig2)

        # Download filtered data
        st.markdown("### 📥 Download Filtered Data")
        csv_ind = filtered_ind_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download as CSV", csv_ind, "filtered_technical_indicator.csv", "text/csv")


# ---------------------------------------------------------------------------------------------------------
    elif view == "Smart Trade Signals":
        st.subheader("📈 Smart Trade Signals – Multi-signal Strategy")

        df_combo = df_chart_ind_data.copy()

        # Step 1: Sentiment Score
        sentiment_score_map = {'Positive': 2, 'Neutral': 1, 'Negative': 0}
        df_combo['Sentiment_Score'] = df_combo['final_sentiment'].map(sentiment_score_map)

        # Step 2: Count chart patterns
        df_combo['Chart_Count'] = df_combo['Chart_Pattern'].fillna('').apply(lambda x: len(x.split(', ')) if x else 0)

        # Step 3: Count technical indicators
        df_combo['Indicator_Count'] = df_combo['Tech_Indicator'].fillna('').apply(lambda x: len(x.split(', ')) if x else 0)

        # Step 4: Total Score
        df_combo['Total_Score'] = df_combo['Sentiment_Score'] + df_combo['Chart_Count'] + df_combo['Indicator_Count']

        # Step 5: Max Score to normalize
        max_possible_score = df_combo['Total_Score'].max()
        df_combo['Success_Chance (%)'] = ((df_combo['Total_Score'] / max_possible_score) * 100).round(2)

        # Step 6: Recommendation logic
        def get_recommendation(score):
            if score >= 6:
                return "BUY"
            elif score >= 4:
                return "HOLD"
            else:
                return "SELL"

        df_combo['Recommendation'] = df_combo['Total_Score'].apply(get_recommendation)

        # Show columns that matter
        st.markdown("### 🧠 Combined Analysis Results")
        display_cols = ['Company', 'Time', 'final_sentiment', 'Chart_Pattern', 'Tech_Indicator', 
                        'Sentiment_Score', 'Chart_Count', 'Indicator_Count', 
                        'Total_Score', 'Success_Chance (%)', 'Recommendation']
        
        st.dataframe(df_combo[display_cols].sort_values(by='Success_Chance (%)', ascending=False))

        # Download Button
        csv_combo = df_combo[display_cols].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Recommendations", csv_combo, "smart_trade_signals.csv", "text/csv")


# ---------------------------------------------------------------------------------------------------------

    # candle chart sentiment distribution
    if st.session_state.last_data is not None:
        st.plotly_chart(create_sentiment_chart(st.session_state.last_data), use_container_width=True)
        st.plotly_chart(create_confidence_chart(st.session_state.last_data), use_container_width=True)


    if st.session_state.last_update:
        st.sidebar.write(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

    # Auto-refresh logic (discouraged to use sleep in Streamlit; better with st_autorefresh)
    if auto_refresh:
        
        st_autorefresh(interval=5 * 60 * 1000, key="datarefresh")
    

# ---------------------------------------------------------------------------------------------------------
    

if __name__ == "__main__":
    main()