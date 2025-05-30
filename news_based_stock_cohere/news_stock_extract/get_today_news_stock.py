"""
python news_stock_extract\get_today_news_stock.py
python -m news_stock_extract.get_today_news_stock
"""
import cohere
import csv
import re
from pathlib import Path
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from news_stock_extract.config import settings

co = cohere.Client(settings["COHERE_API_KEY"])

today = datetime.now().strftime("%d-%b-%Y").lower()

def build_stock_news_prompt():
    
    return f"""
📅 Date: {today}

🔍 Prompt:
Give me a **comprehensive list of today’s stock-related news** for the **Indian stock market**, covering **as many individual stocks as possible** (including large-cap, mid-cap, and small-cap).

Use **trusted sources** only:
- Moneycontrol
- Economic Times
- BSE India
- NSE India
- Reuters
- Bloomberg Quint
- LiveMint
- Trade Brains
- Groww
- Army Recognition

🧾 The news should include key stock-related topics such as:
- 📊 Quarterly Results
- 💰 Earnings Updates
- 📦 New Orders Received
- 🧠 Mergers, Acquisitions, Strategic Decisions
- 📅 Company Events (Board Meetings, Dividend Announcements, etc.)
- 📈 Major Developments impacting stock performance

🔍 Additional Requirement:

After identifying the news from trusted sources, analyze each news item for sentiment (whether it is positive or negative for the stock).
Ensure that all news items are strictly from give date

🪄 **Output Instructions:**
- Format strictly as a **markdown table**
- Use **simple English**, clear and professional
- Do **not** include any explanations or extra text
- Try to include **at least 15–25 rows** if possible

📋 **Output Format Example:**

| Stock Name        | Description (Short Summary)                              | News Type            | News Sentiment     | News Source      |
|-------------------|----------------------------------------------------------|-----------------------|-------------------|------------------|
| Example Ltd       | Q4 profit up by 23%, declared ₹3/share dividend          | Quarterly Result      | Positive           | Moneycontrol     |
| ABC Motors        | Received ₹1500 Cr EV order from Govt                     | New Order             | Negative           | Economic Times   |
| XYZ Pharma        | Launching new cancer drug next week                      | Company Event         | Negative           | LiveMint         |

⚠️ Answer should be in **simple English** and only in **table format**, without extra explanation.
"""

def parse_cohere_table(response_text: str):
    rows = []
    lines = response_text.strip().splitlines()
    for line in lines:
        if re.match(r"^\|", line) and not re.match(r"^\|[-]+\|", line):
            parts = [col.strip() for col in line.strip('|').split('|')]
            if len(parts) == 5:
                rows.append(parts)
    return rows

def save_to_csv(rows, file_path=None):
    if file_path is None:
        file_path = f"stock_news_today_{today}.csv"
    with open(file_path, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    print(f"Saved stock news to {file_path}")

def get_stock_news_from_cohere():
    print("Fetching today's stock news using Cohere Chat")
    prompt = build_stock_news_prompt()
    response = co.chat(message=prompt, temperature=0.5, max_tokens=1000)
    response_text = response.text.strip()
    rows = parse_cohere_table(response_text)
    save_to_csv(rows)

if __name__ == "__main__":
    get_stock_news_from_cohere()
