@echo off
echo ============================================
echo   Intent-to-Cart Application
echo ============================================
echo.

:: Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found. Running first-time setup...
    echo.
    call SETUP.bat
    if errorlevel 1 exit /b 1
    echo.
    echo Setup complete! Now starting the application...
    echo.
    timeout /t 3 /nobreak >nul
)

:: Start the backend
echo Starting backend server...
echo (This will open in the current window)
echo.
echo To start the frontend, open a NEW terminal and run:
echo   START_FRONTEND.bat
echo.
echo Or simply double-click START_FRONTEND.bat
echo.
timeout /t 5 /nobreak >nul

call START_APP.bat
