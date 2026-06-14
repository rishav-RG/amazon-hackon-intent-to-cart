@echo off
echo ============================================
echo   Starting Frontend (React)
echo ============================================
echo.

cd frontend

echo Checking for node_modules...
if not exist "node_modules\" (
    echo Installing dependencies...
    npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo.
echo ============================================
echo   Frontend will start on http://localhost:3000
echo ============================================
echo.
echo Press Ctrl+C to stop the frontend server
echo ============================================
echo.

npm start
