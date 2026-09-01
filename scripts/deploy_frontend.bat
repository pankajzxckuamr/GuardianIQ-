@echo off
setlocal

:: ==============================================================================
:: GuardianIQ Frontend Deployment Script (Windows)
:: ==============================================================================

set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..\
set FRONTEND_DIR=%ROOT_DIR%frontend

echo ==================================================
echo   Deploying GuardianIQ Frontend Layer (Windows)   
echo ==================================================

cd /d "%FRONTEND_DIR%"

:: 1. Check Node.js
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js / npm is not installed or not in PATH.
    exit /b 1
)

:: 2. Configure environment file if missing
if not exist .env (
    if exist .env.example (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env
    )
)

:: 3. Install dependencies
echo [INFO] Installing frontend dependencies...
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed.
    exit /b 1
)

:: 4. Build production bundle
echo [INFO] Building production distribution...
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed.
    exit /b 1
)

echo [SUCCESS] Production build created in frontend\dist.

:: 5. Optional Serve
if "%1"=="serve" (
    echo [INFO] Starting production client server...
    call npm run serve
)

endlocal
