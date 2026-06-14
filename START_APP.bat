@echo off
echo ============================================
echo   Intent-to-Cart Application Launcher
echo ============================================
echo.

:: Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo [1/5] Starting PostgreSQL and Redis with Docker...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start Docker containers!
    pause
    exit /b 1
)

echo [2/5] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo [3/5] Activating Python virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    echo Make sure .venv exists. Run: python -m venv .venv
    pause
    exit /b 1
)

echo [4/5] Running database migrations...
cd backend
alembic upgrade head
if errorlevel 1 (
    echo [WARNING] Database migration failed. This might be okay on first run.
)

echo [5/5] Starting backend server...
echo.
echo ============================================
echo   Backend will start on http://localhost:8000
echo   API docs: http://localhost:8000/docs
echo ============================================
echo.
echo To start the frontend, open a new terminal and run:
echo   cd frontend
echo   npm start
echo.
echo Press Ctrl+C to stop the backend server
echo ============================================
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
