#!/usr/bin/env bash
set -e

# ==============================================================================
# GuardianIQ Background Worker & Scheduler Script (Linux/macOS)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/backend"

echo "=================================================="
echo "  Starting GuardianIQ Background Worker           "
echo "=================================================="

cd "$BACKEND_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONPATH="$BACKEND_DIR"

echo "[INFO] Launching Celery worker..."
exec celery -A app.celery_app.celery_app worker --loglevel=INFO -c 4
