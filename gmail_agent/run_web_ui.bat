@echo off
echo ============================================================
echo Job Email Analyzer - Web Dashboard Launcher
echo ============================================================
echo.

cd /d "%~dp0"

if not exist "..\.venv\" (
    echo Creating virtual environment...
    python -m venv ..\.venv
)

echo Activating virtual environment...
call ..\.venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r ..\requirements.txt --quiet

echo.
echo Starting web server...
echo Dashboard will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python web_ui.py
