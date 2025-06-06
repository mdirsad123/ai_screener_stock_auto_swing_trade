"""
python -m stock_news_analysis.main
"""

import os
import pandas as pd
from datetime import date
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from stock_news_analysis.analysis.extract_text_from_pdf import extract_text_from_bse_pdf, extract_text_from_nse_xml
from stock_news_analysis.analysis.clean_extracted_text import advanced_clean_extracted_text
# from stock_news_analysis.analysis.text_summarization import summarize_text
from stock_news_analysis.analysis.sentiment_analysis import analyze_sentiment
from stock_news_analysis.analysis.read_latest_csv import load_latest_data, load_new_data_to_process
from stock_news_analysis.analysis.data_save_csv import save_to_csv_after_sentiment
from utility.my_automation_logger import get_logger
from utility.debbuger_port_driver import get_driver
from stock_news_analysis.scraping_data_screener.csv_data_nse_annoucement_scrap import get_nse_annoucement_data
from stock_news_analysis.scraping_data_screener.chart_pattern_scrap import fetch_all_patterns_and_indicators
from stock_news_analysis.analysis.data_save_csv import save_to_csv_chart_ind

logger = get_logger('screener_announcements')

def process_row(index, total, row):
    pdf_link = row.get("ATTACHMENT")
    company = row.get("SYMBOL", "Unknown")
    headline = row.get("SUBJECT", "")
    description = row.get("DETAILS", "")
    time_str = row.get("BROADCAST DATE/TIME", "")

    if not pdf_link:
        logger.warning(f"⚠️ Missing PDF link for company: {company}")
        return None

    logger.info(f"📄 [{index}/{total}] Processing PDF for company: {company}")
    try:
        # Choose extractor based on file type
        if pdf_link.lower().endswith(".pdf"):
            text = extract_text_from_bse_pdf(pdf_link)
        elif pdf_link.lower().endswith(".xml"):
            # text = extract_text_from_nse_xml(pdf_link)
            return
        else:
            logger.warning(f"⚠️ Unsupported file type for link: {pdf_link}")
            return None
        
        if not text or not text.strip():
            logger.warning(f"⚠️ Empty or whitespace-only text extracted from {pdf_link}")
            return None
        
        text = advanced_clean_extracted_text(text[300:5000])

        # if len(text) > 2000:
        #     logger.info("🔍 Using summarization due to long text...")
        #     summary = summarize_text(text)
        # else:
        #     summary = text

        sentiment_data = analyze_sentiment(text)

        sentiment_scores = sentiment_data[0]
        final_sentiment = sentiment_data[1]

        vader_score = sentiment_scores.get('vader')
        textblob_score = sentiment_scores.get('textblob')
        bert_sentiment = sentiment_scores.get('transformer')
        confidence = sentiment_scores.get('confidence')

        if bert_sentiment is None:
            logger.warning(f"⚠️ Missing 'transformer' sentiment for {pdf_link}")
            return None

        return {
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
        }
    except Exception as e:
        logger.error(f"❌ Error processing {pdf_link}: {e}")
        return None

def main():
    try:
        df = load_new_data_to_process()
        processed_rows = []
        failed_links = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            total = len(df)
            futures = {
                executor.submit(process_row, idx + 1, total, row): row
                for idx, (_, row) in enumerate(df.iterrows())
            }
            for future in as_completed(futures):
                result = future.result()
                row = futures[future]
                if result:
                    processed_rows.append(result)
                else:
                    failed_links.append(row.get("ATTACHMENT"))

        if processed_rows:
            save_to_csv_after_sentiment(processed_rows)
        else:
            logger.info("No valid PDFs were processed.")

        if failed_links:
            failed_df = pd.DataFrame({"Failed_PDFs": failed_links})
            failed_df.to_csv("failed_pdfs.csv", index=False)
            logger.info(f"⚠️ Saved {len(failed_links)} failed PDF links to 'failed_pdfs.csv'.")

    except Exception as e:
        logger.error(f"❌ Failed to read CSV or process data: {e}")

if __name__ == "__main__":
    start = time.time()
    driver = get_driver()
    get_nse_annoucement_data(driver)
    time.sleep(1)  # Ensure data is downloaded before processing
    main()
    time.sleep(1)

    data = fetch_all_patterns_and_indicators(driver)
    save_to_csv_chart_ind(data)

    end = time.time()
    logger.info(f"✅ All New Data Processed in {end - start:.2f} seconds")
