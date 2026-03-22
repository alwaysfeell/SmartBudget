#!/bin/bash
# SmartBudget — start production environment (Gunicorn)
# Usage: bash scripts/start_prod.sh

set -e

APP_DIR="/opt/smartbudget/app"
VENV_DIR="/opt/smartbudget/venv"
LOG_DIR="/var/log/smartbudget"
ENV_FILE="$APP_DIR/.env"

echo "=== SmartBudget Production Start ==="

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
    echo "Loaded config from $ENV_FILE"
else
    echo "ERROR: .env file not found at $ENV_FILE"
    exit 1
fi

# Check gunicorn
if [ ! -f "$VENV_DIR/bin/gunicorn" ]; then
    echo "Installing gunicorn..."
    "$VENV_DIR/bin/pip" install gunicorn -q
fi

mkdir -p "$LOG_DIR"

echo "Starting Gunicorn on 127.0.0.1:5000 (2 workers)..."
"$VENV_DIR/bin/gunicorn" \
    --workers 2 \
    --bind 127.0.0.1:5000 \
    --access-logfile "$LOG_DIR/access.log" \
    --error-logfile "$LOG_DIR/error.log" \
    --chdir "$APP_DIR" \
    app:app
