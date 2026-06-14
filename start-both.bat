@echo off
echo ========================================
echo Starting Intent-to-Cart Full Stack
echo ========================================
echo.

REM Start backend in a new window
echo Starting Backend Server (FastAPI)...
start "Backend - FastAPI" cmd /k "cd backend && ..\.venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
echo Starting Frontend Server (React)...
start "Frontend - React" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo Both servers are starting...
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window
echo (Servers will continue running)
echo ========================================
pause >nul
