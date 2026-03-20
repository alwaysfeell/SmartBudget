#!/bin/bash
# SmartBudget — комплексна перевірка коду
# Використання: make check  або  bash scripts/check.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "========================================"
echo "  SmartBudget — Комплексна перевірка"
echo "========================================"
echo ""

# 1. Перевірка синтаксису
echo "[1/3] Перевірка синтаксису Python..."
SYNTAX_ERRORS=0
for f in $(find . -name "*.py" \
    -not -path "./__pycache__/*" \
    -not -path "./venv/*" \
    -not -path "./.venv/*" \
    -not -name "lint.py"); do
  if ! python3 -m py_compile "$f" 2>/dev/null; then
    echo "  ❌ Синтаксична помилка: $f"
    SYNTAX_ERRORS=$((SYNTAX_ERRORS+1))
  fi
done
if [ "$SYNTAX_ERRORS" -eq 0 ]; then
  echo "  ✅ Синтаксис: всі файли коректні"
fi

echo ""

# 2. Статичний аналіз (власний лінтер)
echo "[2/3] Статичний аналіз (lint.py)..."
python3 lint.py .

echo ""

# 3. Статична типізація (mypy)
echo "[3/3] Статична типізація (mypy)..."
if command -v mypy &> /dev/null; then
  mypy app.py models/ controllers/ \
    --ignore-missing-imports \
    --no-error-summary 2>&1 | head -30
  echo "  ✅ mypy завершено"
else
  echo "  ⚠️  mypy не встановлено. Виконайте: pip install mypy"
  echo "      або: pip install -r requirements-dev.txt"
fi

echo ""
echo "========================================"
echo "  Перевірку завершено"
echo "========================================"
