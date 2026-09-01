#!/usr/bin/env bash
set -e

# ==============================================================================
# GuardianIQ Unified Deployment Manager (Linux/macOS)
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function print_usage() {
    echo "Usage: ./deploy.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all              Deploy full stack natively (DB migrations, Backend, Frontend build)"
    echo "  --db               Deploy & migrate Database layer only"
    echo "  --backend          Deploy Backend layer only"
    echo "  --frontend         Build and prepare Frontend layer only"
    echo "  --docker           Deploy full stack using Docker Compose"
    echo "  --docker-prod      Deploy production stack using docker-compose.prod.yml"
    echo "  --verify           Run deployment verification smoke tests"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh --db --seed       # Migrate and seed DB"
    echo "  ./deploy.sh --docker          # Start local docker containers"
    echo "  ./deploy.sh --verify          # Verify services"
}

if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    print_usage
    exit 0
fi

ACTION="$1"
shift || true

case "$ACTION" in
    --all)
        echo "[INFO] Running full native deployment..."
        "$ROOT_DIR/scripts/deploy_database.sh" "$@"
        "$ROOT_DIR/scripts/deploy_frontend.sh" build
        "$ROOT_DIR/scripts/deploy_backend.sh"
        ;;
    --db)
        "$ROOT_DIR/scripts/deploy_database.sh" "$@"
        ;;
    --backend)
        "$ROOT_DIR/scripts/deploy_backend.sh" "$@"
        ;;
    --frontend)
        "$ROOT_DIR/scripts/deploy_frontend.sh" "$@"
        ;;
    --docker)
        echo "[INFO] Starting full stack with Docker Compose..."
        docker compose -f "$ROOT_DIR/docker-compose.yml" up --build -d
        echo "[INFO] Containers started in background."
        ;;
    --docker-prod)
        echo "[INFO] Starting production stack with docker-compose.prod.yml..."
        docker compose -f "$ROOT_DIR/docker-compose.prod.yml" up --build -d
        echo "[INFO] Production containers running."
        ;;
    --verify)
        echo "[INFO] Verifying deployment..."
        python3 "$ROOT_DIR/scripts/verify_deployment.py" "$@"
        ;;
    *)
        echo "[ERROR] Unknown option: $ACTION"
        print_usage
        exit 1
        ;;
esac
