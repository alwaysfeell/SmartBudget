@echo off
REM SmartBudget — start development environment (Windows)
REM Usage: scripts\start_dev.bat

echo === SmartBudget Dev Start ===

REM Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM Create venv if missing
IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

REM Set environment variables
set FLASK_ENV=development
set DEBUG=true
set DATABASE=smartbudget.db
set SECRET_KEY=dev-secret-key-not-for-production

echo Starting Flask development server...
echo Open: http://127.0.0.1:5000
echo Press Ctrl+C to stop.
echo.

python app.py
pause
