"""
python screener_folder/top_gainers_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# Screener Top Gainers URL
url = "https://www.screener.in/screens/602651/todays-top-gainers-losers/?sort=return+over+1day&order=desc"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Scrape top 10 stocks
rows = soup.select("table tbody tr")[:10]

data = []
today = datetime.today().strftime('%d-%m-%Y')

for row in rows:
    cols = row.find_all("td")
    if len(cols) < 12:
        continue

    symbol = cols[1].text.strip()
    price = cols[2].text.strip()
    percent_change = cols[11].text.strip()
    volume = cols[8].text.strip()

    data.append({
        "Symbol": symbol,
        "Price": price,
        "%Change": percent_change,
        "Volume": volume,
        "Date": today
    })

# Convert to DataFrame
df = pd.DataFrame(data)

# Save to your specific path
output_path = r"D:\Stock_market\NSE-Stock-Scanner\output\screener_top_gainers.csv"
df.to_csv(output_path, index=False)

print(f"✅ Data saved to: {output_path}")
