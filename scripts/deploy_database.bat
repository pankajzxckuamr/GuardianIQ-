@echo off
setlocal

:: ==============================================================================
:: GuardianIQ Database Deployment Script (Windows)
:: ==============================================================================

set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..\
set BACKEND_DIR=%ROOT_DIR%backend

echo ==================================================
echo   Deploying GuardianIQ Database Layer (Windows)   
echo ==================================================

cd /d "%BACKEND_DIR%"
if exist venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo [INFO] Running Python database deployment orchestrator...
python scripts\deploy_database.py %*

if %errorlevel% neq 0 (
    echo [ERROR] Database deployment failed.
    exit /b %errorlevel%
)

echo ==================================================
echo   Database deployment step completed.             
echo ==================================================
endlocal
