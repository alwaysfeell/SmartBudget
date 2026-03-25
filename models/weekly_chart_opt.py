"""
models/weekly_chart_opt.py — оптимізована версія get_weekly_chart_data.

Оптимізація: агрегація по тижнях виконується на стороні SQLite
(strftime + GROUP BY) замість завантаження всіх рядків у pandas.
"""

from models.utils import get_budget

def get_weekly_chart_data(db) -> dict:
    """Return weekly spending aggregated via SQL instead of pandas.

    Optimisation: uses SQLite strftime('%W', date) + GROUP BY to
    aggregate per-week totals server-side, drastically reducing
    the number of rows transferred into Python.

    Args:
        db: Active SQLite database connection (flask.g.db).

    Returns:
        dict: Keys 'labels' (list[str]) and 'values' (list[float]).
    """
    rows = db.execute("""
        SELECT
            strftime('%Y-W%W', date) AS week,
            ROUND(SUM(price * qty), 2) AS total
        FROM expenses
        GROUP BY week
        ORDER BY week
        LIMIT 12
    """).fetchall()

    labels = [r['week'] for r in rows]
    values = [float(r['total']) for r in rows]

    return {'labels': labels, 'values': values}
