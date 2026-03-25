"""
benchmark_compare.py — порівняння оригінальних та оптимізованих функцій.

Запуск:
    python benchmark_compare.py

Виводить таблицю "до / після" з відсотком покращення.
Результати зберігаються у docs/performance/benchmark_results.txt
"""

import sys
import os
import time
import sqlite3
import tracemalloc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

OUTPUT_DIR = os.path.join(BASE_DIR, 'docs', 'performance')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_test_db(n_rows: int = 500) -> sqlite3.Connection:
    """Створює in-memory SQLite з тестовими даними."""
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    con.execute("""
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, budget REAL DEFAULT 14000)
    """)
    con.execute("""
        CREATE TABLE expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, category TEXT, price REAL,
            qty INTEGER, store TEXT, date TEXT
        )
    """)
    con.execute("INSERT INTO users VALUES (1,'Test',14000)")

    import random, datetime
    random.seed(42)
    stores     = ['Сільпо', 'АТБ', 'Новус', 'Метро', 'Фора', 'Ашан']
    products   = ['Молоко', 'Хліб', 'Масло', 'Сир', 'Яйця', 'Кава', 'Чай',
                  'Цукор', 'Сіль', 'Олія', 'Шампунь', 'Зубна паста', 'Мило',
                  'Пральний порошок', 'Навушники', 'Кабель USB', 'Футболка', 'Шкарпетки']
    cats       = {'Молоко': 'Продукти', 'Хліб': 'Продукти', 'Масло': 'Продукти',
                  'Сир': 'Продукти', 'Яйця': 'Продукти', 'Кава': 'Продукти',
                  'Чай': 'Продукти', 'Цукор': 'Продукти', 'Сіль': 'Продукти',
                  'Олія': 'Продукти', 'Шампунь': 'Побутова хімія',
                  'Зубна паста': 'Побутова хімія', 'Мило': 'Побутова хімія',
                  'Пральний порошок': 'Побутова хімія', 'Навушники': 'Електроніка',
                  'Кабель USB': 'Електроніка', 'Футболка': 'Одяг', 'Шкарпетки': 'Одяг'}
    bases      = {'Молоко': 38, 'Хліб': 25, 'Масло': 85, 'Сир': 120, 'Яйця': 55,
                  'Кава': 180, 'Чай': 65, 'Цукор': 40, 'Сіль': 18, 'Олія': 75,
                  'Шампунь': 95, 'Зубна паста': 70, 'Мило': 35,
                  'Пральний порошок': 145, 'Навушники': 450,
                  'Кабель USB': 120, 'Футболка': 280, 'Шкарпетки': 65}
    today = datetime.date.today()
    rows  = []
    for _ in range(n_rows):
        prod  = random.choice(products)
        store = random.choice(stores)
        d     = (today - datetime.timedelta(days=random.randint(0, 180))).isoformat()
        price = round(bases.get(prod, 50) * random.uniform(0.85, 1.3), 2)
        rows.append((prod, cats.get(prod, 'Інше'), price,
                     random.randint(1, 3), store, d))
    con.executemany(
        'INSERT INTO expenses (name,category,price,qty,store,date) VALUES (?,?,?,?,?,?)',
        rows
    )
    con.commit()
    return con

RUNS = 10

def bench(fn, db):
    """Виконує fn(db) RUNS разів, повертає (mean_ms, peak_kb)."""
    times = []
    peak_kb = 0.0
    for _ in range(RUNS):
        tracemalloc.start()
        t0 = time.perf_counter()
        fn(db)
        elapsed = (time.perf_counter() - t0) * 1000
        _, pk = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        times.append(elapsed)
        peak_kb = max(peak_kb, pk / 1024)
    return round(sum(times) / len(times), 2), round(peak_kb, 1)

def main():
    db = make_test_db(500)

    from models.advice            import generate_advice as advice_orig
    from models.advice_optimized  import generate_advice as advice_opt
    from models.stats             import get_stats
    from models.dss.forecast      import get_forecast
    from models.weekly_chart_opt  import get_weekly_chart_data as chart_opt
    from models.charts            import get_weekly_chart_data as chart_orig

    def orig_advice(d): return advice_orig(d, count=6)
    def opt_advice(d):  return advice_opt(d, count=6)

    cases = [
        ('generate_advice×6',    orig_advice,            opt_advice),
        ('get_weekly_chart_data', chart_orig,             chart_opt),
        ('get_stats',            get_stats,               get_stats),
        ('get_forecast',         get_forecast,            get_forecast),
    ]

    print("=" * 75)
    print("SmartBudget — Порівняння до / після оптимізації")
    print(f"Кількість запусків: {RUNS}, рядків у БД: 500")
    print("=" * 75)
    header = f"{'Функція':<28} {'До (ms)':>8} {'Після (ms)':>11} {'Покращення':>12} {'Пік пам KB':>11}"
    print(header)
    print("-" * 75)

    lines = [header, "-" * 75]
    for name, orig_fn, opt_fn in cases:
        orig_ms, orig_kb = bench(orig_fn, db)
        opt_ms,  opt_kb  = bench(opt_fn, db)
        if orig_ms > 0:
            pct = round((orig_ms - opt_ms) / orig_ms * 100, 1)
        else:
            pct = 0.0
        sign = "▼" if pct > 0 else ("▲" if pct < 0 else "─")
        line = (f"{name:<28} {orig_ms:>8.2f} {opt_ms:>11.2f} "
                f"{sign}{abs(pct):>10.1f}% {opt_kb:>11.1f}")
        print(line)
        lines.append(line)

    print("=" * 75)

    out_path = os.path.join(OUTPUT_DIR, 'benchmark_results.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"\nРезультати збережено: {out_path}")


if __name__ == '__main__':
    main()
