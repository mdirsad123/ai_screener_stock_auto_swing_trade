@echo off
echo Activating virtual environment...
call .venv\Scripts\activate


echo Starting Streamlit application...
streamlit run app.py