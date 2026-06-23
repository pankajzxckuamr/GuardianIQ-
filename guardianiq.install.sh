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



cd "$BACKEND_DIR"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
python -m pip install --upgrade pip
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

# Verify the superuser credentials up front so failures are not silently swallowed.
if ! psql -U postgres -h localhost -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
  echo "[ERROR] Could not connect to PostgreSQL as superuser 'postgres' with the password provided."
  echo "        Check the password (the one you set when installing PostgreSQL) and re-run."
  exit 1
fi

echo "[INFO] Creating database and user..."
# Idempotent role creation; always (re)set the password so it matches backend/.env.
psql -U postgres -h localhost -d postgres -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'guardianiq_user') THEN
    CREATE ROLE guardianiq_user LOGIN PASSWORD 'guardianiq123';
  ELSE
    ALTER ROLE guardianiq_user WITH LOGIN PASSWORD 'guardianiq123';
  END IF;
END
$$;
SQL

# CREATE DATABASE cannot run inside a DO block / transaction, so guard it separately.
if ! psql -U postgres -h localhost -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'guardianiq';" | grep -q 1; then
  psql -U postgres -h localhost -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE guardianiq OWNER guardianiq_user;"
fi

psql -U postgres -h localhost -d postgres -v ON_ERROR_STOP=1 -c "ALTER DATABASE guardianiq OWNER TO guardianiq_user;"
psql -U postgres -h localhost -d postgres -v ON_ERROR_STOP=1 -c "GRANT ALL PRIVILEGES ON DATABASE guardianiq TO guardianiq_user;"
# PostgreSQL 15+ no longer grants CREATE on the public schema by default,
# so make guardianiq_user own the public schema or migrations will fail.
psql -U postgres -h localhost -d guardianiq -v ON_ERROR_STOP=1 -c "ALTER SCHEMA public OWNER TO guardianiq_user;"
psql -U postgres -h localhost -d guardianiq -v ON_ERROR_STOP=1 -c "GRANT ALL ON SCHEMA public TO guardianiq_user;"

echo "[INFO] Running database migrations..."
alembic upgrade head

echo "[INFO] Running database seed..."
python3 -m app.db.seed

deactivate

echo
echo "[SUCCESS] All dependencies installed."
