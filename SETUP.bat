@echo off
echo ============================================
echo   Intent-to-Cart - First Time Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Creating Python virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/4] Installing Python dependencies...
pip install --upgrade pip
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies!
    pause
    exit /b 1
)

echo [4/4] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo [WARNING] Failed to install npm dependencies. You may need to install Node.js.
    cd ..
) else (
    cd ..
)

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Make sure Docker Desktop is running
echo   2. Run START_APP.bat to start the backend
echo   3. Run START_FRONTEND.bat to start the frontend
echo.
echo Or follow the instructions in QUICK_START.md
echo.
pause
