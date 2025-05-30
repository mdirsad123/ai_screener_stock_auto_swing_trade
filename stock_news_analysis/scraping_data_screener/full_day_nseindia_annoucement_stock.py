"""
python -m stock_news_analysis.scraping_data_screener.full_day_nseindia_annoucement_stock
"""

import re
import os
import time
import pandas as pd
from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ProcessPoolExecutor
from datetime import timedelta
from stock_news_analysis.analysis.preprocess import advanced_clean_extracted_text
from stock_news_analysis.analysis.extract_text_from_pdf import extract_text_from_bse_pdf
from stock_news_analysis.analysis.sentiment_analysis import analyze_sentiment
from utility.debbuger_port_driver import get_driver
from utility.my_automation_logger import get_logger
from .chart_pattern_scrap import fetch_all_patterns_and_indicators, save_to_csv_chart_ind

logger = get_logger('screener_announcements')
today_str = date.today().isoformat()
CSV_FILE = Path(__file__).resolve().parent.parent / "output" / f"screener_bse_announcements_{today_str}.csv"
URL = "https://www.bseindia.com/corporates/ann.html"

def fetch_announcements(driver, seen_headlines=None):
    """
    Scrapes the latest announcements from bseindia.com and returns new ones in a structured format.
    """
    announcements = []
    seen_headlines = seen_headlines or set()

    wait = WebDriverWait(driver, 30)
    driver.get(URL)
    logger.info("🚀 Opened BSE India announcement page")

    # Step 1: Calculate yesterday's date in dd/mm/yyyy
    yesterday = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

    # Step 2: Locate and set date using JavaScript
    from_date_field = wait.until(EC.presence_of_element_located((By.ID, "txtFromDt")))
    to_date_field = wait.until(EC.presence_of_element_located((By.ID, "txtToDt")))

    # Set value and manually trigger 'change' event
    driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('change'));
    """, from_date_field, yesterday)

    driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('change'));
    """, to_date_field, yesterday)

    # Step 1: Select 'Result'
    select_element = wait.until(EC.presence_of_element_located((By.ID, "ddlPeriod")))
    Select(select_element).select_by_visible_text("Result")
    logger.info("✅ Selected 'Result' from dropdown")
    time.sleep(1)

    # Step 2: Select 'Financial Results'
    select_element = wait.until(EC.presence_of_element_located((By.ID, "ddlsubcat")))
    Select(select_element).select_by_visible_text("Financial Results")
    logger.info("✅ Selected 'Financial Results' from dropdown")
    time.sleep(1)

    # Step 3: Submit
    submit_button = wait.until(EC.element_to_be_clickable((By.ID, "btnSubmit")))
    time.sleep(0.5)
    submit_button.click()

    submit_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='col-lg-2 text-left']//input[@type='submit' and @value='Submit']")
    ))
    time.sleep(0.5)
    submit_button.click()
    logger.info("🟢 Clicked on Submit button")

    time.sleep(1)

    while True:
        # Step 4: Wait for container and parse announcements on current page
        container = wait.until(EC.presence_of_element_located((By.XPATH, "//tbody/tr[4]/td[1]")))
        tables = container.find_elements(By.TAG_NAME, "table")

        for index, table in enumerate(tables):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                card = [row.find_elements(By.TAG_NAME, "td") for row in rows]
                card_data = [[cell.text.strip() for cell in row if cell.text.strip()] for row in card if row]

                if len(card_data) < 3:
                    continue  # Skip malformed

                headline_raw = card_data[0][0] if card_data[0] else "Unknown"
                description = card_data[1][0] if len(card_data) > 1 and card_data[1] else ""
                timestamp_line = card_data[2][0] if len(card_data) > 2 and card_data[2] else ""

                company_match = re.match(r"^(.*?)\s+-\s+\d{6}\s+-", headline_raw)
                company = company_match.group(1).strip() if company_match else "Unknown"

                time_match = re.search(r'Exchange Disseminated Time ([\d:-]+\s[\d:]+)', timestamp_line)
                time_str = time_match.group(1) if time_match else "Unknown Time"

                headline_parts = headline_raw.split(" - ")
                headline = headline_parts[-1].strip() if len(headline_parts) > 1 else headline_raw.strip()

                unique_id = f"{company}|{headline}|{time_str}"
                if unique_id in seen_headlines:
                    continue

                pdf_link_element = table.find_element(By.XPATH, ".//a[contains(@href, 'pdf')]")
                pdf_link = pdf_link_element.get_attribute('href') if pdf_link_element else None
                if not pdf_link:
                    logger.warning(f"⚠️ PDF link missing for {company} - skipping")
                    continue

                full_text = extract_text_from_bse_pdf(pdf_link)
                Annoucement_Description = advanced_clean_extracted_text(full_text[400:2000])

                sentiment_analysis_data = analyze_sentiment(Annoucement_Description)
                vader_score = sentiment_analysis_data[0]['vader']
                textblob_score = sentiment_analysis_data[0]['textblob']
                bert_sentiment = sentiment_analysis_data[0]['transformer']
                confidence = sentiment_analysis_data[0]['confidence']
                final_sentiment = sentiment_analysis_data[1]

                announcements.append({
                    "Company": company,
                    "Headline": headline,
                    "Description": description,
                    "Time": time_str,
                    "pdf_link": pdf_link,
                    "vader_score": vader_score,
                    "textblob_score": textblob_score,
                    "bert_sentiment": bert_sentiment,
                    "confidence": confidence,
                    "final_sentiment": final_sentiment
                })
                seen_headlines.add(unique_id)

            except Exception as e:
                logger.error(f"❌ Error parsing table #{index}: {e}")

        # Check if "Next" button is present and clickable
        try:
            next_button = driver.find_element(By.ID, "idnext")
            if next_button.is_displayed() and next_button.is_enabled():
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)  # Give time for next page to load
            else:
                break
        except:
            logger.info("🔚 No more pages to fetch.")
            break

    logger.info(f"✅ Parsed {len(announcements)} new announcements")
    return announcements

def save_to_csv(new_data):
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    columns = ["Company", "Headline", "Description", "Time", "pdf_link", "vader_score", "textblob_score", "bert_sentiment", "confidence", "final_sentiment"]

    if CSV_FILE.exists() and CSV_FILE.stat().st_size > 0:
        try:
            old_df = pd.read_csv(CSV_FILE)
            old_links = set(old_df["pdf_link"])
        except Exception as e:
            logger.warning(f"⚠️ Failed to read existing CSV: {e}")
            old_links = set()
            old_df = pd.DataFrame(columns=columns)

        new_entries = [row for row in new_data if row["pdf_link"] not in old_links]
        if new_entries:
            pd.DataFrame(new_entries).to_csv(CSV_FILE, mode='a', header=False, index=False)
            logger.info(f"✅ Appended {len(new_entries)} new rows.")
        else:
            logger.info("ℹ️ No new announcements.")
    else:
        pd.DataFrame(new_data, columns=columns).to_csv(CSV_FILE, index=False)
        logger.info(f"✅ Created new CSV with {len(new_data)} entries: {CSV_FILE.name}")

def test_data(driver, seen_headlines=None):
    """
    Scrapes the latest announcements from bseindia.com and returns new ones in a structured format.
    """
    announcements = []
    seen_headlines = seen_headlines or set()

    wait = WebDriverWait(driver, 30)
    driver.get(URL)
    logger.info("🚀 Opened BSE India announcement page")

    # Step 1: Calculate yesterday's date in dd/mm/yyyy
    yesterday = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

    # Step 2: Locate and set date using JavaScript
    from_date_field = wait.until(EC.presence_of_element_located((By.ID, "txtFromDt")))
    to_date_field = wait.until(EC.presence_of_element_located((By.ID, "txtToDt")))

    # Set value and manually trigger 'change' event
    driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('change'));
    """, from_date_field, yesterday)

    driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('change'));
    """, to_date_field, yesterday)

    # Step 1: Select 'Result'
    select_element = wait.until(EC.presence_of_element_located((By.ID, "ddlPeriod")))
    Select(select_element).select_by_visible_text("Result")
    logger.info("✅ Selected 'Result' from dropdown")
    time.sleep(1)

    # Step 2: Select 'Financial Results'
    select_element = wait.until(EC.presence_of_element_located((By.ID, "ddlsubcat")))
    Select(select_element).select_by_visible_text("Financial Results")
    logger.info("✅ Selected 'Financial Results' from dropdown")
    time.sleep(1)

    # Step 3: Submit
    submit_button = wait.until(EC.element_to_be_clickable((By.ID, "btnSubmit")))
    time.sleep(0.5)
    submit_button.click()

    submit_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='col-lg-2 text-left']//input[@type='submit' and @value='Submit']")
    ))
    time.sleep(0.5)
    submit_button.click()
    logger.info("🟢 Clicked on Submit button")

    time.sleep(1)
    import pdb; pdb.set_trace()  # Debugging breakpoint

    while True:
        # Step 4: Wait for container and parse announcements on current page
        container = wait.until(EC.presence_of_element_located((By.XPATH, "//tbody/tr[4]/td[1]")))
        tables = container.find_elements(By.TAG_NAME, "table")

        for index, table in enumerate(tables):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                card = [row.find_elements(By.TAG_NAME, "td") for row in rows]
                card_data = [[cell.text.strip() for cell in row if cell.text.strip()] for row in card if row]

                if len(card_data) < 3:
                    continue  # Skip malformed

                headline_raw = card_data[0][0] if card_data[0] else "Unknown"
                description = card_data[1][0] if len(card_data) > 1 and card_data[1] else ""
                timestamp_line = card_data[2][0] if len(card_data) > 2 and card_data[2] else ""

                company_match = re.match(r"^(.*?)\s+-\s+\d{6}\s+-", headline_raw)
                company = company_match.group(1).strip() if company_match else "Unknown"

                time_match = re.search(r'Exchange Disseminated Time ([\d:-]+\s[\d:]+)', timestamp_line)
                time_str = time_match.group(1) if time_match else "Unknown Time"

                headline_parts = headline_raw.split(" - ")
                headline = headline_parts[-1].strip() if len(headline_parts) > 1 else headline_raw.strip()

                unique_id = f"{company}|{headline}|{time_str}"
                if unique_id in seen_headlines:
                    continue

                pdf_link_element = table.find_element(By.XPATH, ".//a[contains(@href, 'pdf')]")
                pdf_link = pdf_link_element.get_attribute('href') if pdf_link_element else None
                if not pdf_link:
                    logger.warning(f"⚠️ PDF link missing for {company} - skipping")
                    continue

                full_text = extract_text_from_bse_pdf(pdf_link)
                Annoucement_Description = advanced_clean_extracted_text(full_text[400:2000])

                sentiment_analysis_data = analyze_sentiment(Annoucement_Description)
                vader_score = sentiment_analysis_data[0]['vader']
                textblob_score = sentiment_analysis_data[0]['textblob']
                bert_sentiment = sentiment_analysis_data[0]['transformer']
                confidence = sentiment_analysis_data[0]['confidence']
                final_sentiment = sentiment_analysis_data[1]

                announcements.append({
                    "Company": company,
                    "Headline": headline,
                    "Description": description,
                    "Time": time_str,
                    "pdf_link": pdf_link,
                    "vader_score": vader_score,
                    "textblob_score": textblob_score,
                    "bert_sentiment": bert_sentiment,
                    "confidence": confidence,
                    "final_sentiment": final_sentiment
                })
                seen_headlines.add(unique_id)

            except Exception as e:
                logger.error(f"❌ Error parsing table #{index}: {e}")

        # Check if "Next" button is present and clickable
        try:
            next_button = driver.find_element(By.ID, "idnext")
            if next_button.is_displayed() and next_button.is_enabled():
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)  # Give time for next page to load
            else:
                break
        except:
            logger.info("🔚 No more pages to fetch.")
            break

    logger.info(f"✅ Parsed {len(announcements)} new announcements")
    return announcements


if __name__ == "__main__":
    start = time.time()
    driver = get_driver()
    try:
        seen = set()
        data = fetch_announcements(driver, seen)
        # data = test_data(driver, seen)
        save_to_csv(data)
        time.sleep(2)
        chart_ind_data = fetch_all_patterns_and_indicators(driver)
        save_to_csv_chart_ind(chart_ind_data)
    finally:
        driver.quit()
    end = time.time()
    logger.info(f"✅ All New Data Get in {end - start:.2f} seconds")
