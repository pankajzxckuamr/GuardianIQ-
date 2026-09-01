#!/usr/bin/env bash
set -e

# ==============================================================================
# GuardianIQ Backend Deployment Script (Linux/macOS)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/backend"

echo "=================================================="
echo "  Deploying GuardianIQ Backend Layer              "
echo "=================================================="

cd "$BACKEND_DIR"

# 1. Ensure Python Virtual Environment
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# 2. Install dependencies
echo "[INFO] Installing/upgrading backend dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Check environment file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[WARNING] .env not found. Creating .env from .env.example..."
        cp .env.example .env
    else
        echo "[ERROR] .env file is missing."
        exit 1
    fi
fi

# 4. Run database migrations & setup
echo "[INFO] Running database migrations..."
python scripts/deploy_database.py

# 5. Start Backend Server (Uvicorn or Gunicorn)
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
MODE="${1:-prod}"

if [ "$MODE" = "dev" ]; then
    echo "[INFO] Starting Backend in DEVELOPMENT mode on http://${HOST}:${PORT}..."
    exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
    echo "[INFO] Starting Backend in PRODUCTION mode on http://${HOST}:${PORT}..."
    if command -v gunicorn >/dev/null 2>&1; then
        exec gunicorn -c gunicorn_conf.py app.main:app
    else
        exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers 4
    fi
fi
