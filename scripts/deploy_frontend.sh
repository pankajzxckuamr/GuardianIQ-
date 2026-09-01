#!/usr/bin/env bash
set -e

# ==============================================================================
# GuardianIQ Frontend Deployment Script (Linux/macOS)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "=================================================="
echo "  Deploying GuardianIQ Frontend Layer             "
echo "=================================================="

cd "$FRONTEND_DIR"

# 1. Verify Node.js & npm
if ! command -v npm >/dev/null 2>&1; then
    echo "[ERROR] npm is not installed. Please install Node.js (>= 18)."
    exit 1
fi

echo "[INFO] Node version: $(node -v)"
echo "[INFO] NPM version: $(npm -v)"

# 2. Configure environment file if missing
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[INFO] Creating .env from .env.example..."
        cp .env.example .env
    fi
fi

# 3. Install dependencies
echo "[INFO] Installing frontend dependencies..."
npm install

# 4. Build production bundle
echo "[INFO] Building production bundle (Vite + Server)..."
npm run build

echo " Production build created in frontend/dist"

# 5. Serve or finalize
ACTION="${1:-serve}"

if [ "$ACTION" = "serve" ]; then
    echo "[INFO] Starting production Express static server on port ${PORT:-5173}..."
    exec npm run serve
elif [ "$ACTION" = "dev" ]; then
    echo "[INFO] Starting Vite development server..."
    exec npm run dev
else
    echo "[INFO] Build completed. Artifacts ready in frontend/dist."
fi
