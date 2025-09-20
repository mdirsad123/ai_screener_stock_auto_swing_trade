![ai_stock_screen_4](https://github.com/user-attachments/assets/87a36c5d-0404-4339-9cbb-a1d38e27b507)
![ai_stock_screen_1](https://github.com/user-attachments/assets/d7fa41e5-8967-44bf-8f99-7b6ce7689ea0)
![ai_stock_screen_5](https://github.com/user-attachments/assets/13561822-3a2b-4dfa-936c-3de17fcd96bb)
![ai_stock_screen_2](https://github.com/user-attachments/assets/a8132f55-5a5a-4b75-bd9b-4e69181bbdb3)
![ai_stock_screen_3](https://github.com/user-attachments/assets/3ea8940e-a821-4abb-b925-9d07eda38416)

# 🚀 AI Stock Screener & Auto Swing Trading Pipeline
## Complete Project Documentation

---

### **Project Overview**
This is a sophisticated **AI-powered stock screening and automated swing trading system** that combines multiple data sources and analysis techniques to generate high-confidence trading signals. The system integrates news sentiment analysis, technical indicators, machine learning predictions, and automated order execution to create a comprehensive quantitative trading solution.

---

## **📊 Complete Pipeline Architecture**

### **Phase 1: Data Collection**
```
📥 NSE Announcements → 📄 PDF Extraction → 🔍 Text Processing
```

**Components:**
- **NSE Announcement Scraper** (`csv_data_nse_annoucement_scrap.py`)
  - Scrapes real-time announcements from NSE website
  - Extracts company news, financial reports, and corporate actions
  - Handles both BSE and NSE document formats
- **PDF Text Extraction** (`extract_text_from_pdf.py`)
  - Downloads and extracts text from attached PDF documents
  - Advanced text preprocessing and normalization
- **Text Cleaning** (`clean_extracted_text.py`)
  - Removes noise and standardizes text format

### **Phase 2: Sentiment Analysis**
```
📝 Raw Text → 🤖 Multi-Model Sentiment → 📊 Confidence Scoring
```

**Multi-Model Sentiment Analysis** (`sentiment_analysis.py`):
- **VADER**: Rule-based sentiment analysis for social media text
- **TextBlob**: Statistical sentiment scoring with polarity
- **BERT/Transformer**: Deep learning-based sentiment analysis
- **Ensemble Method**: Combines all models with confidence weighting

**Final Sentiment Classification:**
- Very Positive (Score: 3)
- Positive (Score: 2)
- Neutral (Score: 1)
- Negative (Score: 0)
- Very Negative (Score: 0)

### **Phase 3: Technical Analysis**
```
📈 Stock Data → 🎯 Technical Indicators → 📊 Pattern Recognition
```

**Stock Data Fetcher** (`ml_analysis/src/data_fetcher.py`):
- Fetches historical price data using yfinance
- Updates daily stock information
- Handles multiple stock symbols

**Technical Indicators** (`ml_analysis/src/technical_analysis.py`):
- **Trend Indicators**: 
  - SMA_20 (Simple Moving Average)
  - EMA_20 (Exponential Moving Average)
  - MACD (Moving Average Convergence Divergence)
  - Supertrend
- **Momentum Indicators**: 
  - RSI (Relative Strength Index)
  - ADX (Average Directional Index)
- **Volume Indicators**: 
  - CMF (Chaikin Money Flow)

**Chart Pattern Scanner** (`chart_pattern_scrap.py`):
- Scrapes ChartInk for technical patterns
- Identifies key patterns:
  - Resistance Breakout
  - Volume Spike
  - FII/DII buying patterns

### **Phase 4: Machine Learning**
```
📊 Technical Features → 🤖 ML Model → 📊 Prediction Signals
```

**Model Training** (`ml_analysis/src/model_trainer.py`):
- Uses historical data with technical indicators
- Trains multiple models:
  - XGBoost
  - LightGBM
  - Random Forest
  - Support Vector Machines
- Selects best performing model based on accuracy metrics

**Signal Prediction** (`ml_analysis/src/model_predictor.py`):
- Generates binary signals: "STRONG BUY" or "HOLD/SELL"
- Provides confidence scores (0-1) for predictions
- Uses latest technical indicators for real-time predictions

### **Phase 5: Signal Integration & Scoring**
```
🔗 Multi-Source Data → ⚖️ Weighted Scoring → 🎯 Trading Signals
```

**Scoring Algorithm:**
```python
Total_Score = (Sentiment_Score × 1.5) + (Pattern_Score × 1.3) + (ML_Boost)
Success_Chance = (Total_Score / Max_Possible_Score) × 100
```

**Pattern Weights:**
- Resistance Breakout: 5 points
- Volume Spike: 5 points
- FII/DII Buying: Variable based on amount

**ML Boost Calculation:**
- STRONG BUY: ML_Confidence × 10
- HOLD/SELL: 0

**Signal Categories:**
- **STRONG BUY**: Score ≥ 15, Success Chance ≥ 80%
- **BUY**: Score ≥ 10
- **WATCH**: Score ≥ 6
- **NO TRADE**: Score < 6

### **Phase 6: Automated Trading Execution**
```
🎯 Trading Signals → 🤖 Order Placement → 📱 Notifications
```

**GTT Order Placement** (`algo_trading/gtt_order_place.py`):
- Places Good Till Triggered orders on Upstox
- Implements risk management:
  - Entry price: Current market price
  - Target: +10% from entry
  - Stop Loss: -3% from entry
- Handles order status tracking

**WhatsApp Alerts** (`notification/watsapp_alert_Twilio.py`):
- Real-time trade execution notifications
- Sends comprehensive trade details:
  - Stock symbol and current price
  - Confidence scores and patterns
  - Entry, target, and stop-loss levels
  - Risk-reward ratio

### **Phase 7: Dashboard & Monitoring**
```
📊 Real-time Dashboard → 🔄 Auto-refresh → 📈 Performance Tracking
```

**Streamlit Dashboard** (`app.py`):
- **Real-time Analytics:**
  - Sentiment distribution charts
  - Trading signal visualization
  - Performance metrics
- **Controls:**
  - Manual/automatic trading toggle
  - Pipeline execution buttons
  - Auto-refresh settings
- **Data Visualization:**
  - Interactive charts with Plotly
  - Filterable data tables
  - Download capabilities

---

## **🔄 Complete Workflow Diagram**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NSE Website   │───▶│  PDF Documents  │───▶│  Text Extraction│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Stock Data     │───▶│  Technical      │───▶│  ML Predictions │
│  (yfinance)     │    │  Indicators     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Sentiment      │───▶│  Signal         │───▶│  Trading        │
│  Analysis       │    │  Integration    │    │  Execution      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  WhatsApp       │◀───│  Order          │◀───│  Dashboard      │
│  Notifications  │    │  Placement      │    │  Monitoring     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## **🎯 Key Features & Capabilities**

### **1. Multi-Source Data Integration**
- **News Sentiment**: Real-time corporate announcements analysis
- **Technical Analysis**: 9+ technical indicators and chart patterns
- **Machine Learning**: Historical pattern recognition and prediction
- **Market Data**: Live stock prices and volume data

### **2. Real-time Processing**
- **Automated Pipeline**: Runs every 10 minutes
- **Parallel Processing**: Multi-threaded data processing
- **Error Handling**: Robust error recovery and logging
- **Data Validation**: Quality checks at each stage

### **3. Risk Management**
- **Position Sizing**: Automated based on confidence scores
- **Stop Loss**: -3% automatic stop-loss placement
- **Target Setting**: +10% profit target calculation
- **Portfolio Limits**: Maximum exposure controls

### **4. High Confidence Filtering**
- **Success Threshold**: Only trades with >80% success probability
- **Multi-Factor Validation**: Sentiment + Technical + ML consensus
- **Pattern Confirmation**: Multiple timeframe analysis
- **Volume Confirmation**: High volume breakout validation

### **5. Automated Notifications**
- **Trade Alerts**: Real-time WhatsApp notifications
- **Status Updates**: Order execution confirmations
- **Performance Reports**: Daily/weekly summary reports
- **Error Alerts**: System failure notifications

### **6. Performance Tracking**
- **Real-time Dashboard**: Live performance metrics
- **Historical Analysis**: Backtesting capabilities
- **Risk Metrics**: Sharpe ratio, drawdown analysis
- **Trade Logging**: Complete trade history tracking

---

## **🛠️ Technology Stack**

### **Backend & Core**
- **Python 3.12**: Primary programming language
- **Pandas 2.1.4**: Data manipulation and analysis
- **NumPy 1.26.4**: Numerical computations
- **Scikit-learn 1.4.2**: Machine learning algorithms

### **Machine Learning & AI**
- **TensorFlow 2.16.1**: Deep learning framework
- **PyTorch 2.2.2**: Neural network library
- **Transformers 4.40.0**: BERT and transformer models
- **XGBoost 3.0.2**: Gradient boosting
- **LightGBM 4.6.0**: Light gradient boosting

### **Web Scraping & Automation**
- **Selenium 4.25.0**: Web automation
- **BeautifulSoup 4.12.2**: HTML parsing
- **Requests 2.31.0**: HTTP requests
- **PyAutoGUI 0.9.54**: GUI automation

### **Trading & Market Data**
- **Upstox Python SDK 2.15.0**: Trading API
- **yfinance 0.2.62**: Yahoo Finance data
- **ccxt 4.1.89**: Cryptocurrency exchange library
- **ta 0.11.0**: Technical analysis library

### **Dashboard & Visualization**
- **Streamlit 1.32.0**: Web application framework
- **Plotly 5.19.0**: Interactive charts
- **Matplotlib 3.8.3**: Static plotting
- **Seaborn 0.13.2**: Statistical visualization

### **Notifications & Communication**
- **Twilio 9.6.2**: WhatsApp messaging API
- **Websockets 15.0.1**: Real-time communication
- **pywhatkit 5.4**: WhatsApp automation

### **Data Processing & Storage**
- **PyArrow 14.0.0**: Columnar data format
- **Polars 0.20.6**: Fast DataFrame library
- **PyMuPDF 1.23.25**: PDF processing
- **CSV Files**: Primary data storage format

---

## **📈 Success Metrics & Performance Indicators**

### **Sentiment Analysis Accuracy**
- **Multi-Model Ensemble**: Combines VADER, TextBlob, and BERT
- **Confidence Scoring**: Weighted average of model predictions
- **Validation**: Cross-validation on historical data
- **Accuracy Target**: >85% sentiment classification accuracy

### **Technical Analysis Reliability**
- **Indicator Count**: 9+ technical indicators
- **Pattern Recognition**: Chart pattern identification
- **Signal Confirmation**: Multiple timeframe analysis
- **Success Rate**: Historical backtesting validation

### **Machine Learning Performance**
- **Model Selection**: Best performing model based on accuracy
- **Feature Engineering**: Technical indicator optimization
- **Prediction Accuracy**: >70% signal accuracy
- **Confidence Scoring**: Probability-based predictions

### **Risk Management Effectiveness**
- **Stop Loss**: -3% automatic risk control
- **Target Achievement**: +10% profit target success rate
- **Portfolio Protection**: Maximum exposure limits
- **Drawdown Control**: Maximum 5% portfolio drawdown

### **Execution Speed & Reliability**
- **Processing Time**: <5 minutes for complete pipeline
- **Order Execution**: <30 seconds for GTT order placement
- **System Uptime**: >99% availability
- **Error Recovery**: Automatic retry mechanisms

---

## **🔧 System Architecture**

### **Directory Structure**
```
ai_screener_stock_auto_swing_trade/
├── stock_news_analysis/
│   ├── analysis/           # Sentiment and data analysis
│   ├── scraping_data_screener/  # Web scraping modules
│   ├── algo_trading/       # Trading execution
│   ├── notification/       # Alert systems
│   └── app.py             # Main dashboard
├── ml_analysis/
│   ├── src/               # ML pipeline components
│   └── data/              # Training and processed data
├── utility/               # Common utilities
├── output/                # Generated reports
└── ui/                    # User interface components
```

### **Data Flow Architecture**
1. **Input Layer**: NSE announcements, stock data, PDF documents
2. **Processing Layer**: Sentiment analysis, technical indicators, ML models
3. **Integration Layer**: Signal combination and scoring
4. **Execution Layer**: Order placement and notifications
5. **Monitoring Layer**: Dashboard and performance tracking

### **Scalability Features**
- **Modular Design**: Independent components for easy scaling
- **Parallel Processing**: Multi-threaded data processing
- **Caching**: Intermediate result storage
- **Error Isolation**: Component-level error handling

---

## **🚀 Getting Started**

### **Prerequisites**
- Python 3.12 or higher
- Poetry for dependency management
- Chrome browser for Selenium automation
- Upstox trading account
- Twilio account for WhatsApp notifications

### **Installation**
```bash
# Clone the repository
git clone <repository-url>
cd ai_screener_stock_auto_swing_trade

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### **Configuration**
1. **Trading API**: Configure Upstox API credentials
2. **Notifications**: Set up Twilio WhatsApp integration
3. **Chrome Driver**: Configure Selenium WebDriver
4. **Data Sources**: Verify NSE website access

### **Running the System**
```bash
# Start the dashboard
streamlit run stock_news_analysis/app.py

# Run the complete pipeline
python -m stock_news_analysis.main

# Run ML analysis
python -m ml_analysis.src.main
```

---

## **📊 Performance Monitoring**

### **Key Performance Indicators (KPIs)**
- **Signal Accuracy**: Percentage of profitable trades
- **Win Rate**: Ratio of winning trades to total trades
- **Average Return**: Mean profit per trade
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure

### **Real-time Monitoring**
- **Dashboard Metrics**: Live performance indicators
- **Alert System**: Automated notifications for anomalies
- **Log Analysis**: Comprehensive error and performance logging
- **Backup Systems**: Data redundancy and recovery

---

## **🔮 Future Enhancements**

### **Planned Improvements**
1. **Advanced ML Models**: Deep learning for pattern recognition
2. **Alternative Data**: Social media sentiment, news sentiment
3. **Portfolio Optimization**: Modern portfolio theory integration
4. **Risk Management**: Advanced position sizing algorithms
5. **Mobile App**: Native mobile application for trading

### **Scalability Roadmap**
1. **Cloud Deployment**: AWS/Azure cloud infrastructure
2. **Microservices**: Service-oriented architecture
3. **Real-time Processing**: Apache Kafka integration
4. **Database Integration**: PostgreSQL/MongoDB for data storage
5. **API Development**: RESTful API for external integrations

---

## **📞 Support & Documentation**

### **Contact Information**
- **Developer**: Irshad
- **Project**: AI Stock Screener & Auto Swing Trading
- **Version**: 0.1.0
- **Last Updated**: 2024

### **Documentation**
- **Code Comments**: Comprehensive inline documentation
- **README Files**: Module-specific documentation
- **API Documentation**: Trading and analysis API guides
- **Troubleshooting**: Common issues and solutions

---

*This document provides a comprehensive overview of the AI Stock Screener & Auto Swing Trading system. For detailed implementation, refer to the individual module documentation and source code.* 
