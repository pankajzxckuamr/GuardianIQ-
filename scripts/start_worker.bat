@echo off
setlocal

:: ==============================================================================
:: GuardianIQ Background Worker & Scheduler Script (Windows)
:: ==============================================================================

set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..\
set BACKEND_DIR=%ROOT_DIR%backend

echo ==================================================
echo   Starting GuardianIQ Background Worker (Windows) 
echo ==================================================

cd /d "%BACKEND_DIR%"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

set PYTHONPATH=%BACKEND_DIR%

echo [INFO] Launching Celery worker (solo pool on Windows)...
celery -A app.celery_app.celery_app worker --loglevel=INFO --pool=solo

endlocal
