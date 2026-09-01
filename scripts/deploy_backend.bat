@echo off
setlocal

:: ==============================================================================
:: GuardianIQ Backend Deployment Script (Windows)
:: ==============================================================================

set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..\
set BACKEND_DIR=%ROOT_DIR%backend

echo ==================================================
echo   Deploying GuardianIQ Backend Layer (Windows)    
echo ==================================================

cd /d "%BACKEND_DIR%"

:: 1. Ensure Python Virtual Environment
if not exist venv (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: 2. Install dependencies
echo [INFO] Installing backend dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    exit /b 1
)

:: 3. Check environment file
if not exist .env (
    if exist .env.example (
        echo [WARNING] .env not found. Copying from .env.example...
        copy .env.example .env
    )
)

:: 4. Run database migrations & setup
echo [INFO] Running database migrations...
python scripts\deploy_database.py
if %errorlevel% neq 0 (
    echo [ERROR] Database setup/migration failed.
    exit /b 1
)

:: 5. Start Backend Server
echo [INFO] Starting Backend server on http://localhost:8000...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

endlocal
