from datetime import datetime, timedelta
import pandas as pd
from models.utils import rows_to_df, month_short


def get_weekly_chart_data(db) -> dict:
    """Return weekly spending totals grouped by top category for chart rendering.

    Splits the current month into 7-day intervals and calculates
    spending per category for each interval. Returns data formatted
    for Chart.js grouped bar chart.

    Args:
        db: Active SQLite database connection (flask.g.db).

    Returns:
        dict: Keys:
            labels (list[str]): Week range labels, e.g. ['1–7 Бер', '8–14 Бер'].
            datasets (list[dict]): One dict per top category with keys
                label, data (list[float]), backgroundColor, borderRadius.
    """
    now   = datetime.now()
    start = now.replace(day=1).strftime('%Y-%m-%d')
    rows  = db.execute(
        'SELECT name, category, price, qty, date FROM expenses WHERE date >= ?',
        (start,)
    ).fetchall()
    df = rows_to_df(rows)

    labels, week_ranges = [], []
    d = now.replace(day=1)
    while d.month == now.month:
        w_end = min(d + timedelta(days=6),
                    now.replace(month=d.month % 12 + 1, day=1) - timedelta(days=1))
        labels.append(f'{d.day}–{min(w_end.day, 31)} {month_short(now.month)}')
        week_ranges.append((d.strftime('%Y-%m-%d'), w_end.strftime('%Y-%m-%d')))
        d += timedelta(days=7)
        if d.month != now.month:
            break

    colors = ['rgba(37,99,235,.78)', 'rgba(22,163,74,.7)',
              'rgba(217,119,6,.7)', 'rgba(124,58,237,.7)']

    if df.empty:
        top_cats = ['Продукти', 'Гігієна', 'Побутова хімія']
        return {'labels': labels, 'datasets': [
            {'label': c, 'data': [0]*len(labels),
             'backgroundColor': colors[i], 'borderRadius': 5}
            for i, c in enumerate(top_cats)
        ]}

    df['total'] = df['price'] * df['qty']
    df['date']  = pd.to_datetime(df['date'])
    top_cats    = df.groupby('category')['total'].sum().nlargest(4).index.tolist()

    datasets = []
    for i, cat in enumerate(top_cats):
        cat_df = df[df['category'] == cat]
        data   = [
            round(cat_df[(cat_df['date'] >= ws) & (cat_df['date'] <= we)]['total'].sum(), 2)
            for ws, we in week_ranges
        ]
        datasets.append({'label': cat, 'data': data,
                         'backgroundColor': colors[i % len(colors)], 'borderRadius': 5})
    return {'labels': labels, 'datasets': datasets}


def get_category_chart_data(db) -> dict:
    """Return spending totals grouped by category for pie/bar chart rendering.

    Aggregates current month expenses by category and calculates
    percentage share of each category in total spending.

    Args:
        db: Active SQLite database connection (flask.g.db).

    Returns:
        dict: Keys:
            labels (list[str]): Category names sorted by total descending.
            values (list[float]): Percentage share of each category (sums to 100).
            colors (list[str]): Hex colour codes for each category slice.
    """
    now   = datetime.now()
    start = now.replace(day=1).strftime('%Y-%m-%d')
    rows  = db.execute(
        'SELECT category, price, qty FROM expenses WHERE date >= ?', (start,)
    ).fetchall()
    df = rows_to_df(rows)

    if df.empty:
        return {'labels': [], 'values': [], 'colors': []}

    df['total'] = df['price'] * df['qty']
    grouped     = df.groupby('category')['total'].sum().sort_values(ascending=False)
    pcts        = (grouped / grouped.sum() * 100).round(1)
    palette     = ['#2563eb', '#16a34a', '#d97706', '#7c3aed',
                   '#64748b', '#0891b2', '#be185d', '#ca8a04']
    return {
        'labels': pcts.index.tolist(),
        'values': pcts.values.tolist(),
        'colors': palette[:len(pcts)],
    }


def get_savings_chart_data(db) -> dict:
    """Return monthly realised and potential savings data for the trend chart.

    For each of the last 6 months calculates:
        - actual: savings already achieved (bought below max recorded price).
        - planned: additional savings possible (bought above min recorded price).

    Args:
        db: Active SQLite database connection (flask.g.db).

    Returns:
        dict: Keys:
            labels (list[str]): Month labels, e.g. ['Жов 2024', 'Лис 2024'].
            actual (list[float]): Realised savings per month in UAH.
            planned (list[float]): Potential additional savings per month in UAH.
    """
    rows = db.execute('SELECT name, price, qty, date, store FROM expenses').fetchall()
    df   = rows_to_df(rows)

    now    = datetime.now()
    months, labels = [], []
    for i in range(5, -1, -1):
        m = (now.month - i - 1) % 12 + 1
        y = now.year if now.month - i > 0 else now.year - 1
        months.append((y, m))
        labels.append(f'{month_short(m)} {y}')

    if df.empty:
        return {'labels': labels, 'actual': [0]*6, 'planned': [0]*6}

    df['total'] = df['price'] * df['qty']
    df['date']  = pd.to_datetime(df['date'])
    min_prices  = df[df['store'] != ''].groupby('name')['price'].min()
    max_prices  = df[df['store'] != ''].groupby('name')['price'].max()

    actual, planned = [], []
    for y, m in months:
        month_df = df[(df['date'].dt.year == y) & (df['date'].dt.month == m)]
        if month_df.empty:
            actual.append(0.0); planned.append(0.0); continue

        real_s, pot_s = 0.0, 0.0
        for name, grp in month_df.groupby('name'):
            if name not in min_prices.index:
                continue
            min_p, max_p = float(min_prices[name]), float(max_prices[name])
            for _, row in grp.iterrows():
                paid, qty = float(row['price']), int(row['qty'])
                real_s += (max_p - paid) * qty
                pot_s  += (paid - min_p) * qty

        actual.append(round(max(real_s, 0), 2))
        planned.append(round(max(pot_s, 0), 2))

    return {'labels': labels, 'actual': actual, 'planned': planned}
