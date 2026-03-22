#!/bin/bash
# SmartBudget — backup script
# Usage: bash scripts/backup.sh

set -e

APP_DIR="/opt/smartbudget/app"
DATA_DIR="/opt/smartbudget/data"
BACKUP_DIR="/opt/smartbudget/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# 1. Database
if [ -f "$DATA_DIR/smartbudget.db" ]; then
    cp "$DATA_DIR/smartbudget.db" "$BACKUP_DIR/smartbudget_$TIMESTAMP.db"
    echo "[$(date)] Database backed up: smartbudget_$TIMESTAMP.db"
else
    echo "[$(date)] WARNING: Database file not found at $DATA_DIR/smartbudget.db"
fi

# 2. .env config
if [ -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env" "$BACKUP_DIR/env_$TIMESTAMP.bak"
    echo "[$(date)] Config backed up: env_$TIMESTAMP.bak"
fi

# 3. Rotate old backups
find "$BACKUP_DIR" -name "*.db" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "*.bak" -mtime +$KEEP_DAYS -delete
echo "[$(date)] Old backups (>${KEEP_DAYS} days) removed."

echo "[$(date)] Backup complete. Files in: $BACKUP_DIR"
