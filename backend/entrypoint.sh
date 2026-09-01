#!/bin/sh
set -e

# ==============================================================================
# GuardianIQ Backend Container Entrypoint
# ==============================================================================

echo "=================================================="
echo "  Starting GuardianIQ Backend Container           "
echo "=================================================="

# Check if we should automatically run migrations on startup
if [ "${AUTO_MIGRATE:-true}" = "true" ]; then
    echo "[INFO] Running database migrations & health check..."
    python scripts/deploy_database.py --skip-ddl || {
        echo "[WARNING] Initial migration runner encountered issues. Retrying in 3 seconds..."
        sleep 3
        python scripts/deploy_database.py || true
    }
fi

echo "[INFO] Launching application command: $@"
exec "$@"
