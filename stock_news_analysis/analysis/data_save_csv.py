import pandas as pd
from datetime import date
from pathlib import Path
from utility.my_automation_logger import get_logger

logger = get_logger('Saved_csv_of_after_sentiment_analysis')

today_str = date.today().isoformat()
CSV_FILE = Path(__file__).resolve().parent.parent / "output" / f"process_sentiment_anaylsis_{today_str}.csv"
CSV_FILE_CHART_IND = Path(__file__).resolve().parent.parent / "output" / "chart_pattern_detect" / f"chart_pattern_{today_str}.csv"


def save_to_csv_after_sentiment(new_data):
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

def save_to_csv_chart_ind(df):
    CSV_FILE_CHART_IND.parent.mkdir(parents=True, exist_ok=True)

    try:
        if CSV_FILE_CHART_IND.exists() and CSV_FILE_CHART_IND.stat().st_size > 0:
            df_existing = pd.read_csv(CSV_FILE_CHART_IND)
            df_combined = pd.concat([df_existing, df], ignore_index=True)
            df_combined.drop_duplicates(subset=["Company", "Headline", "Chart_Pattern", "Tech_Indicator"], keep="last", inplace=True)
            df_combined.to_csv(CSV_FILE_CHART_IND, index=False)
            logger.info(f"✅ Updated existing CSV with {len(df)} new/updated rows: {CSV_FILE_CHART_IND.name}")
        else:
            df.to_csv(CSV_FILE_CHART_IND, index=False)
            logger.info(f"✅ Created new CSV with {len(df)} rows: {CSV_FILE_CHART_IND.name}")
    except Exception as e:
        logger.error(f"❌ Error saving CSV: {e}")

if __name__ == "__main__":
    data = ''
    save_to_csv_after_sentiment(data)