#!/usr/bin/env bash
set -e

# ==============================================================================
# GuardianIQ Database Deployment Script (Linux/macOS)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/backend"

echo "=================================================="
echo "  Deploying GuardianIQ Database Layer             "
echo "=================================================="

# Check Python environment
cd "$BACKEND_DIR"
if [ -d "venv" ]; then
    echo "[INFO] Activating virtual environment..."
    source venv/bin/activate
elif command -v python3 >/dev/null 2>&1; then
    echo "[INFO] Using system python3..."
else
    echo "[ERROR] Python 3 is required."
    exit 1
fi

# Parse options
FLAGS="$@"
echo "[INFO] Running Python database deployment orchestrator..."
python3 scripts/deploy_database.py $FLAGS

echo "=================================================="
echo "  Database deployment step completed.             "
echo "=================================================="
