# SmartBudget — Makefile
# Використання: make <target>

.PHONY: help lint typecheck check run install clean

help:
	@echo "SmartBudget — доступні команди:"
	@echo "  make install    — встановити залежності (requirements.txt + requirements-dev.txt)"
	@echo "  make lint       — запустити лінтер (lint.py)"
	@echo "  make typecheck  — статична типізація (mypy)"
	@echo "  make check      — повна перевірка (lint + typecheck)"
	@echo "  make run        — запустити сервер розробки"
	@echo "  make clean      — видалити кеш Python"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

lint:
	@echo "==> Статичний аналіз коду..."
	python3 lint.py .

typecheck:
	@echo "==> Статична типізація (mypy)..."
	@if command -v mypy > /dev/null 2>&1; then \
		mypy app.py models/ controllers/ --ignore-missing-imports; \
	else \
		echo "⚠️  mypy не встановлено. Виконайте: pip install mypy"; \
	fi

check: lint typecheck
	@echo ""
	@echo "✅ Перевірку завершено."

run:
	python3 app.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Кеш очищено."
