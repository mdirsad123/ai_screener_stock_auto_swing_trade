"""
Run as:
python news_stock_extract\get_news_stock_finchat.py
python -m news_stock_extract.get_news_stock_finchat
"""

import csv
import re
import os
import sys
from datetime import datetime
import cohere

# Add parent folder to sys.path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from news_stock_extract.config import settings  # Make sure this file exists and has the API key

# Initialize Cohere client using FinChat API key
co = cohere.Client(settings["FINCHAT_API_KEY"])  # Ensure FINCHAT_API_KEY is correct

def build_stock_news_prompt():
    today = datetime.now().strftime("%d-%b-%Y").lower()
    return f"""
📅 Date: {today}

🔍 Prompt:
Please give me **today’s stock-related news** for the **Indian stock market** from **trusted sources** such as:
- Moneycontrol
- Economic Times
- BSE India
- NSE India
- Reuters
- Bloomberg Quint
- LiveMint
- Trade Brains
- Groww⁠

The news should include topics like:
- 📊 **Quarterly Results**
- 💰 **Earnings Updates**
- 📦 **New Orders Received**
- 📅 **Company Events**
- 📈 **Major Developments Impacting Stock**

🧾 **Output Format (Table Only):**

| Stock Name        | Description (Short Summary)                              | News Type            | News sentiment     | News Source      |
|-------------------|----------------------------------------------------------|-----------------------|-------------------|------------------|
| Example Ltd       | Q4 profit up by 23%, declared ₹3/share dividend          | Quarterly Result      | Positive           | Moneycontrol     |
| ABC Motors        | Received ₹1500 Cr EV order from Govt                     | New Order             | Positive           | Economic Times   |

⚠️ Answer in **markdown table format** only, no extra explanation.
"""

def parse_markdown_table(text):
    rows = []
    lines = text.strip().splitlines()
    for line in lines:
        if re.match(r"^\|", line) and not re.match(r"^\|[-]+\|", line):
            parts = [col.strip() for col in line.strip('|').split('|')]
            if len(parts) == 5:
                rows.append(parts)
    return rows

def save_to_csv(rows, file_path="stock_news_today_finchat.csv"):
    with open(file_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Stock Name", "Description", "News Type", "News Sentiment", "News Source"])
        writer.writerows(rows)
    print(f"✅ Saved stock news to {file_path}")

def get_stock_news_from_finchat():
    prompt = build_stock_news_prompt()
    print("📡 Sending prompt to FinChat AI via Cohere...")
    
    try:
        response = co.chat(message=prompt)
        response_text = response.text.strip()
        rows = parse_markdown_table(response_text)
        if rows:
            save_to_csv(rows)
        else:
            print("⚠️ No valid table rows parsed from the response.")
    except Exception as e:
        print(f"❌ Exception occurred while calling FinChat: {e}")

if __name__ == "__main__":
    get_stock_news_from_finchat()
