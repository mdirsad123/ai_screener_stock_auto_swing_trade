"""
python -m stock_news_analysis.analysis.extract_text_from_pdf
"""

import requests
import fitz  # PyMuPDF
import io

import requests
import fitz  # PyMuPDF
import io
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def extract_text_from_bse_pdf(url: str) -> str:
    """
    Extracts text from a BSE announcement PDF URL.

    Parameters:
        url (str): The full BSE announcement PDF URL.

    Returns:
        str: Extracted text content from the PDF.

    Raises:
        ValueError: If the response is not a PDF.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.bseindia.com/"
    }

    response = requests.get(url, headers=headers)

    if response.headers.get("Content-Type") != "application/pdf":
        raise ValueError(f"Expected a PDF, but got: {response.headers.get('Content-Type')}")

    pdf_file = fitz.open(stream=io.BytesIO(response.content), filetype="pdf")

    full_text = ""
    for page in pdf_file:
        full_text += page.get_text()

    return full_text

def summarize_text(text: str, max_chunk_chars: int = 2000) -> str:
    """
    Summarizes long text in chunks using a transformer model.

    Parameters:
        text (str): The full extracted text.
        max_chunk_chars (int): Max characters per chunk.

    Returns:
        str: Final combined summary.
    """
    chunks = [text[i:i+max_chunk_chars] for i in range(0, len(text), max_chunk_chars)]
    summaries = []

    for chunk in chunks:
        summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])

    return " ".join(summaries)

if __name__ == "__main__":
    url = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/819c4bf5-f4a0-4315-8e5c-ecb6c6165ba0.pdf"
    try:
        text = extract_text_from_bse_pdf(url)
        print("📝befor Summary:")
        print(text[500:5000])
        summary = summarize_text(text)
        print("📝 after Summary:")
        print(summary)

        # Optionally: Run your sentiment analyzer here
        # sentiment, label = analyze_sentiment(summary)
        # print("🔍 Sentiment:", label)

    except ValueError as e:
        print("Failed to extract PDF:", e)

