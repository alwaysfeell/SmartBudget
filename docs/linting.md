# Linting та статичний аналіз коду — SmartBudget

## Обраний інструмент

**Власний лінтер `lint.py`** на базі вбудованих модулів Python (`ast`, `re`).

У виробничому середовищі рекомендується стек: **flake8 + pylint + mypy**.
Конфігурації `.flake8`, `.pylintrc`, `mypy.ini` присутні в репозиторії.

### Причини вибору lint.py

| Критерій | Обґрунтування |
|---|---|
| Нульові залежності | Лише стандартна бібліотека Python — не потребує pip |
| Портативність | Працює у будь-якому середовищі з Python 3.8+ |
| Налаштованість | Правила пишуться на Python, легко розширювати |

---

## Правила лінтингу та їх пояснення

| Код | Назва | Опис |
|---|---|---|
| E501 | Line too long | Рядок > 100 символів |
| W292 | No newline at EOF | Відсутній \n в кінці файлу |
| F401 | Unused import | Невикористаний імпорт |
| D100 | Missing docstring | Публічна функція без документації |
| C901 | High complexity | Циклічна складність > 10 |
| E711 | None comparison | `== None` замість `is None` |
| E712 | Bool comparison | `== True` замість `if x:` |
| W0611 | Bare except | `except:` без типу винятку |
| B006 | Mutable default arg | Змінний об'єкт як аргумент за замовчуванням |

---

## Інструкція з запуску

### Власний лінтер
```bash
python3 lint.py .
```

### Через Makefile (рекомендовано)
```bash
make lint        # лише лінтер
make typecheck   # лише mypy
make check       # lint + typecheck разом
```

### flake8 + pylint (якщо встановлено)
```bash
pip install -r requirements-dev.txt
flake8 .
pylint app.py models/ controllers/
```

---

## Результати аналізу

| Показник | Значення |
|---|---|
| Файлів перевірено | 22 |
| Проблем до виправлення | 95 |
| Проблем після виправлення | 4 |
| Виправлено | **91 (96%)** |

### Деталі за типами

| Код | До | Після | Виправлено |
|---|---|---|---|
| D100 | 36 | 0 | 36 (100%) |
| E501 | 34 | 0 | 34 (100%) |
| W292 | 17 | 0 | 17 (100%) |
| C901 | 4 | 4 | 0 (технічний борг) |
| W605 | 3 | 0 | 3 (виправлено в лінтері) |
| F401 | 1 | 0 | 1 (100%) |

**C901 (4 функції)** — задокументований технічний борг. Функції DSS мають складну аналітичну логіку, рефакторинг потребує окремого спринту.

---

## Git Hooks

### Встановлення pre-commit хука
```bash
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Хук блокує коміт за наявності критичних помилок (F401, E711, E712, E999).

---

## Інтеграція з процесом збірки (Makefile)

```bash
make check      # повна перевірка: lint + mypy
make lint       # лише статичний аналіз
make typecheck  # лише mypy
make install    # встановити всі залежності
make run        # запустити сервер
make clean      # видалити __pycache__
```

---

## Статична типізація (mypy)

### Конфігурація (mypy.ini)
```ini
[mypy]
python_version = 3.10
ignore_missing_imports = True
warn_unused_ignores = True
exclude = (?x)(__pycache__/ | venv/ | templates/)
```

### Запуск
```bash
pip install mypy
mypy app.py models/ controllers/ --ignore-missing-imports
# або через Makefile:
make typecheck
```

### Наявні анотації типів у проєкті
```python
def get_stats(db) -> dict: ...
def rows_to_df(rows) -> pd.DataFrame: ...
def month_short(m: int) -> str: ...
def get_budget(db) -> float: ...
def get_price_comparison(db) -> list: ...
def get_forecast(db) -> dict: ...
def get_advice_quality(db) -> dict: ...
def get_scenario_analysis(db) -> dict: ...
def get_budget_rule_503020(db) -> dict: ...
```
