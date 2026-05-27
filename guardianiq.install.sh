#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[INFO] python3 is not installed. Attempting to install..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
  elif command -v brew >/dev/null 2>&1; then
    brew install python@3.10
  else
    echo "[ERROR] Could not find apt-get or brew. Please install python3 manually."
    exit 1
  fi
fi



python3 -m pip install --upgrade pip

cd "$BACKEND_DIR"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

echo "[INFO] Setting up the database..."
if ! command -v psql >/dev/null 2>&1; then
  echo "[INFO] psql is not installed. Attempting to install PostgreSQL..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib
  elif command -v brew >/dev/null 2>&1; then
    brew install postgresql@14
  else
    echo "[ERROR] Could not find apt-get or brew. Please install postgresql manually."
    exit 1
  fi
fi

echo "[INFO] PostgreSQL is available."
read -s -p "Enter your PostgreSQL superuser (postgres) password: " PGPASSWORD
echo ""
export PGPASSWORD

echo "[INFO] Creating database and user..."
psql -U postgres -c "CREATE DATABASE guardianiq;" 2>/dev/null || true
psql -U postgres -c "CREATE USER guardianiq_user WITH PASSWORD 'guardianiq123';" 2>/dev/null || true
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE guardianiq TO guardianiq_user;" 2>/dev/null || true

echo "[INFO] Running database migrations..."
alembic upgrade head

echo "[INFO] Running database seed..."
python3 -m app.db.seed

deactivate

echo
echo "[SUCCESS] All dependencies installed."
