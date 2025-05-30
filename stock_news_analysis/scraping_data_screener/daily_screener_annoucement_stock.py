"""
python -m stock_news_analysis.scraping_data_screener.daily_screener_annoucement_stock
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
from selenium.webdriver.support import expected_conditions as EC
from stock_news_analysis.analysis.preprocess import advanced_clean_extracted_text
from stock_news_analysis.analysis.extract_text_from_pdf import extract_text_from_bse_pdf
from stock_news_analysis.analysis.extract_text_from_pdf import summarize_text
from stock_news_analysis.analysis.sentiment_analysis import analyze_sentiment
from utility.debbuger_port_driver import get_driver
from utility.my_automation_logger import get_logger

# Configuration
logger = get_logger('screener_announcements')
today_str = date.today().isoformat()
CSV_FILE = Path(__file__).resolve().parent.parent / "output" / f"screener_announcements_{today_str}.csv"
URL = "https://www.screener.in/announcements/all/"


def calculate_announcement_datetime(scraped_at: str, time_ago: str) -> str:
    scraped_time = datetime.fromisoformat(scraped_at)

    # parse '7m ago', '2h ago', etc.
    number = int(re.search(r'\d+', time_ago).group())  # extract number
    unit = re.search(r'[smhd]', time_ago).group()       # extract unit

    if unit == 's':
        delta = timedelta(seconds=number)
    elif unit == 'm':
        delta = timedelta(minutes=number)
    elif unit == 'h':
        delta = timedelta(hours=number)
    elif unit == 'd':
        delta = timedelta(days=number)
    else:
        delta = timedelta(0)

    announcement_time = scraped_time - delta
    return announcement_time.isoformat().replace('T', ' ')


def fetch_announcements(driver, seen_headlines=None):
    """
    Scrapes the latest 5 announcements from Screener.in and returns new ones.
    """
    announcements = []
    seen_headlines = seen_headlines or set()

    wait = WebDriverWait(driver, 30)
    driver.get(URL)
    logger.info("🚀 Opened Screener announcement page")

    # Wait for the main card
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='card card-medium']")))

    # Get latest 5 announcement divs inside the first .card.card-medium
    xpath = "//div[@class='card card-medium']//div[position() > 1 and position() <= 6]"
    divs = driver.find_elements(By.XPATH, xpath)
    logger.info(f"📦 Found {len(divs)} latest announcement blocks")

    for index, div in enumerate(divs):
        try:
            raw_text = div.text.strip()
            lines = raw_text.splitlines()

            if len(lines) < 2:
                continue  # skip malformed blocks

            company = lines[0].strip()
            second_line = lines[1].strip()

            # Extract time (e.g., '3m ago')
            match = re.search(r'\b\d+\s?[smhd] ago\b', second_line)
            time_ago = match.group(0) if match else "0m ago"

            # Remove time from headline
            headline = second_line.replace(time_ago, '').strip()

            # Extract link
            link_element = div.find_element(By.XPATH, ".//a")
            link = link_element.get_attribute("href")

            scraped_at = datetime.now().isoformat()
            announcement_datetime = calculate_announcement_datetime(scraped_at, time_ago)

            xpath = f"//a[contains(normalize-space(.), '{headline}')]"
            element = driver.find_element(By.XPATH, xpath)
            pdf_link = element.get_attribute("href")

            full_text = extract_text_from_bse_pdf(pdf_link)
            summarizer_text = summarize_text(full_text[400:5000])  # Limit to first 2000 characters
            Annoucement_Description = advanced_clean_extracted_text(summarizer_text)

            # fetch sentiment analysis data
            sentiment_analysis_data = analyze_sentiment(Annoucement_Description)
            vader_score = sentiment_analysis_data[0]['vader']
            textblob_score = sentiment_analysis_data[0]['textblob']
            bert_sentiment = sentiment_analysis_data[0]['transformer']
            confidence = sentiment_analysis_data[0]['confidence']
            final_sentiment = sentiment_analysis_data[1]

            unique_id = f"{company}|{headline}|{time_ago}"
            if unique_id not in seen_headlines:
                announcements.append({
                    "Company": company,
                    "Headline": headline,
                    "Time": time_ago,
                    "Link": link,
                    "Scraped_At": scraped_at,
                    "Announcement_Datetime": announcement_datetime,
                    "pdf_link": pdf_link,
                    "Annoucement_Description": Annoucement_Description,
                    "vader_score": vader_score,
                    "textblob_score": textblob_score,
                    "bert_sentiment": bert_sentiment,
                    "confidence": confidence,
                    "final_sentiment": final_sentiment
                })
                seen_headlines.add(unique_id)

        except Exception as e:
            logger.error(f"❌ Error parsing div #{index}: {e}")

    return announcements


def save_to_csv(new_data):
    """
    Saves the given announcement data to a CSV file.
    Appends only new entries if the file already exists.
    Creates headers if file doesn't exist or is empty.
    """
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)

    columns = ["Company", "Headline", "Time", "Link", "Scraped_At", "Announcement_Datetime", "pdf_link", "Annoucement_Description", "vader_score", "textblob_score", "bert_sentiment", "confidence", "final_sentiment"]

    if CSV_FILE.exists() and CSV_FILE.stat().st_size > 0:
        try:
            old_df = pd.read_csv(CSV_FILE)
            old_links = set(old_df["Link"])
        except Exception as e:
            logger.warning(f"⚠️ Failed to read existing CSV: {e}")
            old_links = set()
            old_df = pd.DataFrame(columns=columns)

        new_entries = [row for row in new_data if row["Link"] not in old_links]
        if new_entries:
            pd.DataFrame(new_entries).to_csv(CSV_FILE, mode='a', header=False, index=False)
            logger.info(f"✅ Appended {len(new_entries)} new rows.")
        else:
            logger.info("ℹ️ No new announcements.")
    else:
        pd.DataFrame(new_data, columns=columns).to_csv(CSV_FILE, index=False)
        logger.info(f"✅ Created new CSV with {len(new_data)} entries: {CSV_FILE.name}")


if __name__ == "__main__":
    driver = get_driver()
    try:
        seen = set()
        data = fetch_announcements(driver, seen)
        save_to_csv(data)
    finally:
        driver.quit()
