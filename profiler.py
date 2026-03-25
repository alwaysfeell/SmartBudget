"""
profiler.py — CPU та memory профілювання функцій SmartBudget.

Запуск:
    python profiler.py            # Базовий cProfile
    python profiler.py --detailed # cProfile + memory_profiler

Результати зберігаються у:
    docs/performance/profile_cpu.prof    (для SnakeViz/cProfileV)
    docs/performance/profile_report.txt  (текстовий звіт)
"""

import cProfile
import pstats
import io
import os
import sys
import time
import sqlite3
import tracemalloc

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'docs', 'performance')
os.makedirs(OUTPUT_DIR, exist_ok=True)

sys.path.insert(0, BASE_DIR)

def make_test_db(n_rows: int = 500) -> sqlite3.Connection:
    """Створює in-memory SQLite з тестовими даними (n_rows покупок)."""
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    con.execute("""
        CREATE TABLE users (
            id     INTEGER PRIMARY KEY,
            name   TEXT,
            budget REAL DEFAULT 14000
        )
    """)
    con.execute("""
        CREATE TABLE expenses (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT,
            category TEXT,
            price    REAL,
            qty      INTEGER,
            store    TEXT,
            date     TEXT
        )
    """)
    con.execute("INSERT INTO users VALUES (1,'Test User',14000)")

    import random, datetime
    random.seed(42)
    stores     = ['Сільпо', 'АТБ', 'Новус', 'Метро', 'Фора', 'Ашан']
    categories = ['Продукти', 'Побутова хімія', 'Електроніка', 'Одяг', 'Розваги']
    products   = [
        'Молоко', 'Хліб', 'Масло', 'Сир', 'Яйця',
        'Кава', 'Чай', 'Цукор', 'Сіль', 'Олія',
        'Шампунь', 'Зубна паста', 'Мило', 'Пральний порошок',
        'Навушники', 'Кабель USB', 'Футболка', 'Шкарпетки',
    ]

    today = datetime.date.today()
    rows  = []
    for i in range(n_rows):
        days_ago = random.randint(0, 180)
        d = (today - datetime.timedelta(days=days_ago)).isoformat()
        prod  = random.choice(products)
        store = random.choice(stores)
        base_price = {'Молоко': 38, 'Хліб': 25, 'Масло': 85, 'Сир': 120,
                      'Яйця': 55, 'Кава': 180, 'Чай': 65, 'Цукор': 40,
                      'Сіль': 18, 'Олія': 75, 'Шампунь': 95, 'Зубна паста': 70,
                      'Мило': 35, 'Пральний порошок': 145, 'Навушники': 450,
                      'Кабель USB': 120, 'Футболка': 280, 'Шкарпетки': 65}.get(prod, 50)
        price = round(base_price * random.uniform(0.85, 1.3), 2)
        cat   = {'Молоко': 'Продукти', 'Хліб': 'Продукти', 'Масло': 'Продукти',
                 'Сир': 'Продукти', 'Яйця': 'Продукти', 'Кава': 'Продукти',
                 'Чай': 'Продукти', 'Цукор': 'Продукти', 'Сіль': 'Продукти',
                 'Олія': 'Продукти', 'Шампунь': 'Побутова хімія',
                 'Зубна паста': 'Побутова хімія', 'Мило': 'Побутова хімія',
                 'Пральний порошок': 'Побутова хімія', 'Навушники': 'Електроніка',
                 'Кабель USB': 'Електроніка', 'Футболка': 'Одяг',
                 'Шкарпетки': 'Одяг'}.get(prod, random.choice(categories))
        rows.append((prod, cat, price, random.randint(1, 3), store, d))

    con.executemany(
        'INSERT INTO expenses (name,category,price,qty,store,date) VALUES (?,?,?,?,?,?)',
        rows
    )
    con.commit()
    return con

def run_all_benchmarks(db):
    """Виконує всі ключові функції проєкту та повертає час виконання."""
    from models.stats           import get_stats
    from models.advice          import generate_advice
    from models.charts          import get_weekly_chart_data
    from models.prices          import get_price_comparison
    from models.dss.forecast    import get_forecast
    from models.dss.budget_rule import get_budget_rule_503020

    results = {}

    funcs = [
        ('get_stats',              lambda: get_stats(db)),
        ('generate_advice×6',      lambda: generate_advice(db, count=6)),
        ('get_weekly_chart_data',   lambda: get_weekly_chart_data(db)),
        ('get_price_comparison',   lambda: get_price_comparison(db)),
        ('get_forecast',           lambda: get_forecast(db)),
        ('get_budget_rule_503020', lambda: get_budget_rule_503020(db)),
    ]

    RUNS = 5
    for name, fn in funcs:
        times = []
        for _ in range(RUNS):
            t0 = time.perf_counter()
            fn()
            times.append((time.perf_counter() - t0) * 1000)
        results[name] = {
            'min':  round(min(times),  2),
            'max':  round(max(times),  2),
            'mean': round(sum(times) / len(times), 2),
        }

    return results

def run_cpu_profile(db):
    """Запускає cProfile та зберігає результати."""
    from models.stats           import get_stats
    from models.advice          import generate_advice
    from models.charts          import get_weekly_chart_data
    from models.prices          import get_price_comparison
    from models.dss.forecast    import get_forecast
    from models.dss.budget_rule import get_budget_rule_503020

    pr = cProfile.Profile()
    pr.enable()

    get_stats(db)
    generate_advice(db, count=6)
    get_weekly_chart_data(db)
    get_price_comparison(db)
    get_forecast(db)
    get_budget_rule_503020(db)

    pr.disable()

    prof_path = os.path.join(OUTPUT_DIR, 'profile_cpu.prof')
    pr.dump_stats(prof_path)

    s   = io.StringIO()
    ps  = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)

    return s.getvalue(), prof_path


def run_memory_profile(db):
    """Вимірює споживання пам'яті через tracemalloc."""
    from models.stats           import get_stats
    from models.advice          import generate_advice
    from models.dss.forecast    import get_forecast

    mem_results = {}

    funcs = [
        ('get_stats',         lambda: get_stats(db)),
        ('generate_advice×6', lambda: generate_advice(db, count=6)),
        ('get_forecast',      lambda: get_forecast(db)),
    ]

    for name, fn in funcs:
        tracemalloc.start()
        fn()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        mem_results[name] = {
            'current_kb': round(current / 1024, 1),
            'peak_kb':    round(peak / 1024, 1),
        }

    return mem_results

def main():
    print("=" * 70)
    print("SmartBudget Performance Profiler")
    print("=" * 70)

    print("\n[1/4] Створення тестової БД (500 рядків)...")
    db = make_test_db(500)
    print("      OK")

    print("\n[2/4] Benchmark (5 запусків кожної функції)...")
    bench = run_all_benchmarks(db)
    print(f"{'Функція':<28} {'min,ms':>8} {'mean,ms':>9} {'max,ms':>8}")
    print("-" * 58)
    for fn, m in bench.items():
        print(f"{fn:<28} {m['min']:>8.2f} {m['mean']:>9.2f} {m['max']:>8.2f}")

    print("\n[3/4] CPU profiling (cProfile)...")
    cpu_report, prof_path = run_cpu_profile(db)
    print(f"      Збережено: {prof_path}")
    print("\nTop-20 функцій (cumulative time):")
    print(cpu_report)

    print("\n[4/4] Memory profiling (tracemalloc)...")
    mem = run_memory_profile(db)
    print(f"{'Функція':<28} {'поточна KB':>12} {'пік KB':>9}")
    print("-" * 52)
    for fn, m in mem.items():
        print(f"{fn:<28} {m['current_kb']:>12.1f} {m['peak_kb']:>9.1f}")

    report_path = os.path.join(OUTPUT_DIR, 'profile_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("SmartBudget — Звіт профілювання\n")
        f.write("=" * 70 + "\n\n")

        f.write("BENCHMARK (середній час, 5 запусків, 500 рядків у БД)\n")
        f.write(f"{'Функція':<28} {'min,ms':>8} {'mean,ms':>9} {'max,ms':>8}\n")
        f.write("-" * 58 + "\n")
        for fn, m in bench.items():
            f.write(f"{fn:<28} {m['min']:>8.2f} {m['mean']:>9.2f} {m['max']:>8.2f}\n")

        f.write("\nCPU PROFILE (top-20):\n")
        f.write(cpu_report)

        f.write("\nMEMORY PROFILE (tracemalloc):\n")
        f.write(f"{'Функція':<28} {'поточна KB':>12} {'пік KB':>9}\n")
        f.write("-" * 52 + "\n")
        for fn, m in mem.items():
            f.write(f"{fn:<28} {m['current_kb']:>12.1f} {m['peak_kb']:>9.1f}\n")

    print(f"\nЗвіт збережено: {report_path}")
    print("=" * 70)

    return bench, mem


if __name__ == '__main__':
    main()
