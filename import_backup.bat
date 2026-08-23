@echo off
setlocal

echo ========================================================
echo GuardianIQ Database Importer
echo ========================================================
echo This script will import the GuardianIQ backup file into your local PostgreSQL database.
echo.

set /p PGPASSWORD="Enter your PostgreSQL superuser (postgres) password: "
echo.

echo Importing data from GuardianIQ_Database_Backup.sql...
psql -U postgres -d guardianiq -f "%~dp0database\seed\GuardianIQ_Database_Backup.sql"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Database import completed!
) else (
    echo.
    echo [WARNING] Import finished, but some errors were encountered (e.g., duplicate rows).
)

pause
endlocal
