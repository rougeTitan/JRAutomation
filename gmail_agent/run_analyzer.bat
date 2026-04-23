@echo off
echo ============================================================
echo Job Email Analyzer - Windows Launcher
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
echo Starting Job Email Analyzer...
echo.
python job_analyzer.py

pause
