# docs/performance.md — Профілювання та оптимізація SmartBudget

---

## 1. Інструменти профілювання

| Інструмент | Тип | Застосування |
|---|---|---|
| `cProfile` (stdlib) | CPU-профілювання | Час виконання кожної функції та кількість викликів |
| `pstats` (stdlib) | Аналіз CPU | Сортування та фільтрація результатів cProfile |
| `tracemalloc` (stdlib) | Профілювання пам'яті | Пікове та поточне споживання пам'яті |
| `time.perf_counter` | Бенчмарк | Точний замір часу виконання (мікросекунди) |

Всі інструменти є частиною стандартної бібліотеки Python — без зовнішніх залежностей.

---

## 2. Тестовий сценарій

**Файл:** `profiler.py`

**База даних:** in-memory SQLite, 500 рядків витрат:
- 18 товарів, 6 магазинів, 5 категорій
- Дати: останні 180 днів
- `random.seed(42)` — відтворюваний набір

**Методологія:** базове профілювання — 5 запусків кожної функції, порівняльний бенчмарк — 10 запусків.

---

## 3. Базове профілювання — результати ДО оптимізації

### 3.1 Benchmark (5 запусків, 500 рядків)

| Функція | min, ms | mean, ms | max, ms |
|---|---|---|---|
| `get_stats` | 4.61 | 9.66 | 29.59 |
| `generate_advice×6` | **64.77** | **66.40** | **70.96** |
| `get_weekly_chart_data` | 13.11 | 13.39 | 13.99 |
| `get_price_comparison` | 10.23 | 10.56 | 10.90 |
| `get_forecast` | 4.77 | 5.37 | 7.54 |
| `get_budget_rule_503020` | 2.81 | 2.99 | 3.62 |

### 3.2 Профілювання пам'яті (tracemalloc)

| Функція | Поточна, KB | Пік, KB |
|---|---|---|
| `get_stats` | 17.1 | 333.7 |
| `generate_advice×6` | 18.9 | 464.0 |
| `get_forecast` | 15.3 | 235.5 |

### 3.3 Виявлені "гарячі точки" (cProfile top-3)

1. **`generate_advice` — 0.131 s (65.5% загального часу)**
   - Завантажує всі рядки таблиці в pandas DataFrame
   - `df.groupby('name')['price'].min()` — зайвий прохід по даних
   - Вкладені цикли `for store in groupby → for name in groupby`
   - Зайвий `df.copy()` при першому алгоритмі

2. **`get_weekly_chart_data` — 0.026 s**
   - Завантажує всі 500 рядків у pandas DataFrame
   - Агрегація по тижнях виконується в Python замість SQL GROUP BY

3. **`get_price_comparison` — 0.019 s**
   - Повне сканування таблиці expenses для порівняння цін

---

## 4. Реалізовані оптимізації

### 4.1 `generate_advice` → `models/advice_optimized.py`

**Оптимізація 1 — SQL агрегація min_price:**
```python
# БУЛО:
min_prices = df.groupby('name')['price'].min()

# СТАЛО:
min_rows = db.execute(
    'SELECT name, MIN(price) as min_price FROM expenses '
    'WHERE store != "" GROUP BY name'
).fetchall()
min_prices = {r['name']: r['min_price'] for r in min_rows}
```

**Оптимізація 2 — store_overpay за один прохід:**
```python
# БУЛО: вкладений groupby store → groupby name
# СТАЛО: один прохід по (store, name) кортежах
for (store, name), sgrp in df.groupby(['store', 'name']):
    ...
```

**Оптимізація 3 — видалено зайвий `df.copy()`** у першому алгоритмі.

### 4.2 `get_weekly_chart_data` → `models/weekly_chart_opt.py`

**Оптимізація — агрегація на стороні SQLite:**
```python
# БУЛО: завантаження 500 рядків → pandas resample
# СТАЛО:
rows = db.execute("""
    SELECT strftime('%Y-W%W', date) AS week,
           ROUND(SUM(price * qty), 2) AS total
    FROM expenses
    GROUP BY week ORDER BY week LIMIT 12
""").fetchall()
```

SQLite повертає лише 12 агрегованих рядків замість 500 — передача даних між БД і Python зменшується в ~40 разів.

---

## 5. Результати після оптимізації

### 5.1 Порівняльна таблиця (10 запусків, 500 рядків)

| Функція | До (ms) | Після (ms) | Покращення | Пік пам. KB |
|---|---|---|---|---|
| `generate_advice×6` | 133.11 | 115.94 | **▼ 12.9%** | 588.9 |
| `get_weekly_chart_data` | 25.98 | 0.32 | **▼ 98.8%** | 2.2 |
| `get_stats` | 11.67 | 11.45 | ▼ 1.9% | 332.1 |
| `get_forecast` | 10.84 | 10.75 | ▼ 0.8% | 236.5 |

### 5.2 Нові "гарячі точки"

Після оптимізації `get_weekly_chart_data` (0.32 ms) перестав бути bottleneck.
Найповільнішою функцією залишається `generate_advice` (115.94 ms) через
необхідність виконання 6 незалежних алгоритмів аналізу — це задокументований
технічний борг (складність C901, зафіксована у лабораторній роботі №4).

---

## 6. Запуск профілювання

```bash
python profiler.py           # базове профілювання
python benchmark_compare.py  # порівняння до/після
make profile                 # через Makefile
make benchmark
```
---

## 7. Файли

| Файл | Призначення |
|---|---|
| `profiler.py` | CPU + memory профілювання |
| `benchmark_compare.py` | Порівняння до/після |
| `models/advice_optimized.py` | Оптимізована версія generate_advice |
| `models/weekly_chart_opt.py` | Оптимізована версія get_weekly_chart_data |
| `docs/performance/profile_cpu.prof` | Бінарний .prof файл |
| `docs/performance/profile_report.txt` | Текстовий CPU-звіт |
| `docs/performance/benchmark_results.txt` | Результати бенчмарку |
