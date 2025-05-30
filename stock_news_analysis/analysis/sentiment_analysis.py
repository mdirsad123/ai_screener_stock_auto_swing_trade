"""
Run test:
    python -m stock_news_analysis.analysis.sentiment_analysis
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import numpy as np
import torch.nn.functional as F
import os


# Boost if strong keywords exist
strong_positive_keywords = [
    "acquisition", "record profit", "strong earnings", "merger", "order win",
    "new contracts", "joint venture", "buyback", "dividend", "strategic partnership"
]

# Optional: Language detection (uncomment if needed)
# from langdetect import detect

# Load NLTK VADER
vader_analyzer = SentimentIntensityAnalyzer()

# Load BERTweet model & tokenizer with error handling
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
except Exception as e:
    print(f"[ERROR] Failed to load BERTweet model: {e}")
    tokenizer = None
    model = None

# Transformer labels
labels = ['NEG', 'NEU', 'POS']

class EnhancedSentimentAnalyzer:
    def __init__(self):
        self.vader = vader_analyzer
        self.model = model
        self.tokenizer = tokenizer
        self.labels = labels

    def analyze(self, text):
        if not isinstance(text, str) or not text.strip():
            return {"vader": 0, "textblob": 0, "transformer": 0, "combined": 0, "confidence": 0}, "Neutral"

        # Optional: Detect non-English text
        # try:
        #     lang = detect(text)
        #     if lang != "en":
        #         return {"vader": 0, "textblob": 0, "transformer": 0, "combined": 0, "confidence": 0}, "Non-English"
        # except:
        #     pass

        # VADER
        vader_score = self.vader.polarity_scores(text)['compound']

        # TextBlob
        textblob_score = TextBlob(text).sentiment.polarity

        # Transformer (BERTweet)
        transformer_score = 0
        transformer_raw_scores = [0, 0, 0]

        if self.model is not None and self.tokenizer is not None:
            encoded_input = tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                padding='max_length',
                max_length=512
            )
            with torch.no_grad():
                output = self.model(**encoded_input)
            scores = F.softmax(output.logits, dim=1)[0].numpy()
            transformer_score = float(scores[2] - scores[0])  # POS - NEG
            transformer_raw_scores = scores.tolist()

        # Combine with weighted average
        combined_score = (
            vader_score * 0.4 +
            textblob_score * 0.3 +
            transformer_score * 0.3
        )

        text_lower = text.lower()
        for keyword in strong_positive_keywords:
            if keyword in text_lower:
                combined_score += 0.2  # boost
                break
            
        # Normalize to [-1, 1] if needed (optional)
        combined_score = max(-1, min(1, combined_score))

        # Confidence is the absolute value of combined score
        confidence = abs(combined_score)

        # Categorize
        if combined_score >= 0.7:
            sentiment = "Very Positive"
        elif combined_score >= 0.1:
            sentiment = "Positive"
        elif combined_score <= -0.7:
            sentiment = "Very Negative"
        elif combined_score <= -0.1:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        return {
            "vader": vader_score,
            "textblob": textblob_score,
            "transformer": transformer_score,
            "transformer_scores_raw": transformer_raw_scores,  # Optional: debugging only
            "combined": combined_score,
            "confidence": confidence
        }, sentiment

# Singleton instance
analyzer = EnhancedSentimentAnalyzer()

def analyze_sentiment(text):
    return analyzer.analyze(text)

# Test Run
if __name__ == "__main__":
    result = analyze_sentiment("""the board of directors in their meeting held on may 2025 resolved as follows. approved the audited financial statements and audited financial results for the quarter and financial year ended march 2025 and to publish the same.recommended an equity dividend of rs 0.50 per equity share of rs 10 each. siddharth metals ltd. iates for pharmaceuticals and active pharmaceutical ingredients. revenue from operations 2486.78 euros. other income 23.66 euros. expenses 1350.62 euros. profitlosj from operations before. and after tax 2510.45 euros. riqht share capital1018.25.25251.01825.250101801.01017017.0001.01016.00. noncurrent assets property plant and equipment 4102.96.964334.94.94 4103.96. 4000000. total assets 5523.5523937103.3. liabilities 1433.61.1797.44. alkali metals limited has a total of 9293.63 million shares. the company has a net debt of 1768.77 million pounds. the company has a longterm debt of 3434.23 million pounds and an equity of 4452.48 million pounds as at march 31 2025. the board had recommended an equity dividend of rs 0.50 per share of rs 10 paid up. the audited financial results of the company have been prepared in accordance with indain accounting standards. the company is predominantly engaged in the manufacture and sale of chemicals. report on the audit of the financial results of alkali metals limited. company has identified geographical segments based on location of customers as reportable segments. we conducted our audit in accordance with the standards on auditing sas specified under section 14310 of the companies act 2013. we are independent of the company inaccordance with the code ofethics issued by the institute of chartered accountants of india. we believe that the audit evidence we have acquired is sufficient and appropriate to provide a basis for our opinion. auditors responsibilities lor the audit of the inancial results for the quarter and year ended march 31 2025. board of directors are also responsible for overseeing the companys financialreporting process. fraud may involve collusion forgery purposefully omissions misrepresentations or the override of internal control. erial misstatement resulting from fraud is higher than for one resulting from error. alkali metals limited is an indian metals and mining company based in hyderabad india. the company is a member of the national stock exchange of india and the bombay stock exchange. b. venkatesh babu is in practice since 2002. he is a reputed professional with extensive experience. his expertise includes conducting secretarial audits ipos and compliance audits. for period of 1 year from april 2025 to march 2026. chartered accountants frn have a rich experience in audit taxation due diligence and other related matters.""")

    vader_score = result[0]['vader']
    textblob_score = result[0]['textblob']
    bert_sentiment = result[0]['transformer']
    confidence = result[0]['confidence']
    final_sentiment = result[1]
    print(vader_score, textblob_score, bert_sentiment, confidence, final_sentiment)
