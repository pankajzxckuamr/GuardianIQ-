@echo off
setlocal

:: ==============================================================================
:: GuardianIQ Unified Deployment Manager (Windows)
:: ==============================================================================

set ROOT_DIR=%~dp0

if "%1"=="" goto help
if "%1"=="--help" goto help
if "%1"=="-h" goto help

if "%1"=="--all" goto deploy_all
if "%1"=="--db" goto deploy_db
if "%1"=="--backend" goto deploy_backend
if "%1"=="--frontend" goto deploy_frontend
if "%1"=="--docker" goto deploy_docker
if "%1"=="--docker-prod" goto deploy_docker_prod
if "%1"=="--verify" goto verify_deploy

echo [ERROR] Unknown option: %1
goto help

:deploy_all
echo [INFO] Running full native deployment...
call "%ROOT_DIR%scripts\deploy_database.bat" %2 %3 %4
call "%ROOT_DIR%scripts\deploy_frontend.bat"
call "%ROOT_DIR%scripts\deploy_backend.bat"
goto end

:deploy_db
call "%ROOT_DIR%scripts\deploy_database.bat" %2 %3 %4
goto end

:deploy_backend
call "%ROOT_DIR%scripts\deploy_backend.bat" %2 %3 %4
goto end

:deploy_frontend
call "%ROOT_DIR%scripts\deploy_frontend.bat" %2 %3 %4
goto end

:deploy_docker
echo [INFO] Starting full stack with Docker Compose...
docker compose -f "%ROOT_DIR%docker-compose.yml" up --build -d
goto end

:deploy_docker_prod
echo [INFO] Starting production stack with docker-compose.prod.yml...
docker compose -f "%ROOT_DIR%docker-compose.prod.yml" up --build -d
goto end

:verify_deploy
echo [INFO] Verifying deployment...
cd /d "%ROOT_DIR%backend"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
python "%ROOT_DIR%scripts\verify_deployment.py" %2 %3 %4
goto end

:help
echo Usage: deploy.bat [OPTIONS]
echo.
echo Options:
echo   --all              Deploy full stack natively (DB migrations, Frontend build, Backend)
echo   --db               Deploy ^& migrate Database layer only
echo   --backend          Deploy Backend layer only
echo   --frontend         Build and prepare Frontend layer only
echo   --docker           Deploy full stack using Docker Compose
echo   --docker-prod      Deploy production stack using docker-compose.prod.yml
echo   --verify           Run deployment verification smoke tests
echo   --help             Show this help message
echo.
echo Examples:
echo   deploy.bat --db --seed
echo   deploy.bat --docker
echo   deploy.bat --verify

:end
endlocal
