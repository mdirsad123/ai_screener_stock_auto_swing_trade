"""
python -m stock_news_analysis.main
"""

import os
import pandas as pd
from analysis.extract_text_from_pdf import extract_text_from_bse_pdf
from analysis.preprocess import advanced_clean_extracted_text

def main():
    try:
        # Path to your CSV file
        csv_path = os.path.join("stock_news_analysis", "output", "screener_announcements_2025-05-15.csv")
        
        # Read the CSV
        df = pd.read_csv(csv_path)

        # Add new columns for text processing
        df['extracted_text'] = None
        df['cleaned_text'] = None

        # Loop through each pdf_link
        for index, row in df.iterrows():
            pdf_link = row.get("pdf_link")
            company = row.get("Company", "Unknown")

            if pdf_link:
                print(f"\nProcessing PDF for company: {company}")
                try:
                    # Extract text from PDF
                    text = extract_text_from_bse_pdf(pdf_link)
                    df.at[index, 'extracted_text'] = text
                    print(f"Extracted Text (First 500 chars):\n{text[:500]}")

                    # Clean the text
                    cleaned_text = advanced_clean_extracted_text(text)
                    df.at[index, 'cleaned_text'] = cleaned_text
                    print(f"Cleaned Text (First 500 chars):\n{cleaned_text[:500]}")
                except Exception as e:
                    print(f"Error processing {pdf_link}: {e}")

        # Save the processed data back to CSV
        output_path = os.path.join("stock_news_analysis", "output", "processed_announcements.csv")
        df.to_csv(output_path, index=False)
        print(f"\nProcessed data saved to: {output_path}")

    except Exception as e:
        print(f"Failed to read CSV or process links: {e}")

if __name__ == "__main__":
    main()
