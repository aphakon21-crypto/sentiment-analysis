@echo off
title Retail Sentiment Dashboard
echo Checking system readiness...

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python first.
    pause
    exit
)

:: 2. Install/Update Libraries
echo Checking Libraries (This may take a minute on first run)...
pip install streamlit pandas plotly gspread oauth2client requests --quiet

:: 3. Run Streamlit
echo Launching Dashboard...
streamlit run src/dashboard/app.py

pause