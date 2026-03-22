#!/bin/bash
# SmartBudget — start development environment
# Usage: bash scripts/start_dev.sh

set -e

echo "=== SmartBudget Dev Start ==="

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+"
    exit 1
fi

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Set dev environment variables
export FLASK_ENV=development
export DEBUG=true
export DATABASE=smartbudget.db
export SECRET_KEY=dev-secret-key-not-for-production

echo "Starting Flask development server..."
echo "Open: http://127.0.0.1:5000"
echo "Press Ctrl+C to stop."
echo ""

python app.py
