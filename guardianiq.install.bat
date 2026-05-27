@echo off
setlocal

NET SESSION >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Requesting administrative privileges to bypass shell restrictions and install dependencies...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%backend

where python >nul 2>nul
if errorlevel 1 (
    echo [INFO] Python is not installed. Attempting to install via winget...
    winget install -e --id Python.Python.3.10 --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] Failed to install Python. Please install manually.
        pause
        exit /b 1
    )
    echo [INFO] Python installed successfully. Restarting script to update PATH...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    exit /b 1
)

cd /d "%BACKEND_DIR%"
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies.
    exit /b 1
)

echo [INFO] Setting up the database...
where psql >nul 2>nul
if errorlevel 1 (
    echo [INFO] psql is not installed. Attempting to install PostgreSQL via winget...
    winget install -e --id PostgreSQL.PostgreSQL --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] Failed to install PostgreSQL. Please install manually.
        pause
        exit /b 1
    )
    echo [INFO] PostgreSQL installed successfully. Restarting script to update PATH...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

echo [INFO] PostgreSQL is available.
set /p PGPASSWORD="Enter your PostgreSQL superuser (postgres) password: "

echo [INFO] Creating database and user...
psql -U postgres -c "CREATE DATABASE guardianiq;" 2>nul
psql -U postgres -c "CREATE USER guardianiq_user WITH PASSWORD 'guardianiq123';" 2>nul
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE guardianiq TO guardianiq_user;" 2>nul

echo [INFO] Running database migrations...
alembic upgrade head
if errorlevel 1 (
    echo [ERROR] Failed to run database migrations.
    exit /b 1
)

echo [INFO] Running database seed...
python -m app.db.seed
if errorlevel 1 (
    echo [ERROR] Failed to seed database.
    exit /b 1
)

echo.
echo [SUCCESS] All dependencies installed and project is setup.
pause
endlocal
