"""
python -m stock_news_analysis.scraping_data_screener.chart_pattern_scrap
"""

import re
import os
import time
from datetime import datetime, date, timedelta
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from collections import defaultdict
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utility.debbuger_port_driver import get_driver
from utility.my_automation_logger import get_logger
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
logger = get_logger('screener_announcements')
today_str = date.today().isoformat()
CSV_FILE = Path(__file__).resolve().parent.parent / "output" / "chart_pattern_detect" / f"chart_pattern_{today_str}.csv"

def load_latest_data():
    """Load the latest CSV file from the output directory and filter by datetime range."""
    output_dir = os.path.join("stock_news_analysis", "output")
    if not os.path.exists(output_dir):
        return None

    files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
    if not files:
        return None

    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
    df = pd.read_csv(os.path.join(output_dir, latest_file))

    return df


# Load logger and selenium driver, define load_latest_data() earlier

# Common fetch function
def fetch_single_url(driver, companies, url, label):
    results = defaultdict(list)
    wait = WebDriverWait(driver, 10)
    short_wait = WebDriverWait(driver, 1)
    
    try:
        driver.get(url)
        print(f"Opened: {label} -> {url}")
        time.sleep(2)
        
        for company in companies:
            try:
                search_word = " ".join(company.split()[:2])
                # import pdb; pdb.set_trace()  # Debugging breakpoint
                search_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='search']")))
                search_box.clear()
                search_box.send_keys(search_word)
                time.sleep(1)

                xpath_company = f"//a[starts-with(normalize-space(), '{search_word}')]"
                short_wait.until(EC.presence_of_element_located((By.XPATH, xpath_company)))
                results[company].append(label)
                print(f"✅ {company} -> {label}")
            except TimeoutException:
                continue
            except Exception as e:
                print(f"⚠️ {company} -> {label} ERROR: {e}")
                continue
    except Exception as e:
        print(f"❌ Error in {label} scraping: {e}")
    
    return results

def fetch_parallel_chartink(driver, companies, url_label_dict):
    all_results = defaultdict(list)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_single_url, driver, companies, url, label): label
            for url, label in url_label_dict.items()
        }
        for future in as_completed(futures):
            result = future.result()
            for k, v in result.items():
                all_results[k].extend(v)
    return all_results

def fetch_all_patterns_and_indicators(driver):
    df = load_latest_data()
    if df is None or 'Company' not in df.columns:
        print("Error loading data or missing 'Company' column")
        return pd.DataFrame()

    companies = df['Company'].dropna().unique().tolist()

    pattern_urls = {
        "https://chartink.com/screener/copy-cup-handle-breakout-pattern-with-high-volume": "Cup and Handle",
        "https://chartink.com/screener/daily-double-bottom": "Double Bottom",
        # "https://chartink.com/screener/falling-wedge-pattern": "Falling Wedge",
        "https://chartink.com/screener/bull-flag-scanner": "Bull Flag",
        "https://chartink.com/screener/resistance-breakout-with-high-volume": "Resistance Breakout",
        "https://chartink.com/screener/volume-spike-daily": "Volume Spike",
        # "https://chartink.com/screener/inverse-head-and-shoulders-6": "Inverse Head and Shoulders"
    }

    indicator_urls = {
        "https://chartink.com/screener/macd-bearish-or-bullish-crossover": "MACD Crossover",
        # "https://chartink.com/screener/rsi-indicator": "RSI Signal",
        "https://chartink.com/screener/supertrend-screener": "Supertrend",
        # "https://chartink.com/screener/adx-indicator": "ADX Signal",
        # "https://chartink.com/screener/cmf-68": "CMF Signal",
        # "https://chartink.com/screener/golden-cross-scan":"Golden Cross"
    }

    pattern_results = fetch_parallel_chartink(driver, companies, pattern_urls)
    indicator_results = fetch_parallel_chartink(driver, companies, indicator_urls)

    df['Chart_Pattern'] = df['Company'].apply(lambda x: ', '.join(pattern_results.get(x, [])))
    df['Tech_Indicator'] = df['Company'].apply(lambda x: ', '.join(indicator_results.get(x, [])))
    return df

def save_to_csv_chart_ind(df):
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        if CSV_FILE.exists() and CSV_FILE.stat().st_size > 0:
            df_existing = pd.read_csv(CSV_FILE)
            df_combined = pd.concat([df_existing, df], ignore_index=True)
            df_combined.drop_duplicates(subset=["Company", "Headline", "Chart_Pattern", "Tech_Indicator"], keep="last", inplace=True)
            df_combined.to_csv(CSV_FILE, index=False)
            logger.info(f"✅ Updated existing CSV with {len(df)} new/updated rows: {CSV_FILE.name}")
        else:
            df.to_csv(CSV_FILE, index=False)
            logger.info(f"✅ Created new CSV with {len(df)} rows: {CSV_FILE.name}")
    except Exception as e:
        logger.error(f"❌ Error saving CSV: {e}")

if __name__ == "__main__":
    driver = get_driver()
    data = fetch_all_patterns_and_indicators(driver)
    print(data)
    save_to_csv_chart_ind(data)
    driver.quit()
