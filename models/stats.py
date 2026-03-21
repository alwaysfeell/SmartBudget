from datetime import datetime, timedelta
import pandas as pd
from models.utils import rows_to_df


def get_stats(db) -> dict:
    """Return budget statistics for the current and previous month.

    Calculates total spending, budget utilization percentage,
    month-over-month percentage change, remaining budget,
    and potential savings based on price comparison across stores.

    Args:
        db: Active SQLite database connection (flask.g.db).

    Returns:
        dict: Keys:
            budget (float): Monthly budget limit.
            spent (float): Total spent in the current month.
            spent_prev (float): Total spent in the previous month.
            pct_change (float): Month-over-month change in percent.
            remaining (float): Budget minus current spending.
            budget_pct (float): Percentage of budget used (capped at 100).
            savings (float): Potential savings from cheaper store alternatives.
            total_purchases (int): Number of purchases this month.
    """
    user   = db.execute('SELECT budget FROM users WHERE id=1').fetchone()
    budget = user['budget'] if user else 14000.0

    now        = datetime.now()
    start      = now.replace(day=1).strftime('%Y-%m-%d')
    prev_end   = (now.replace(day=1) - timedelta(days=1))
    prev_start = prev_end.replace(day=1).strftime('%Y-%m-%d')
    prev_end   = prev_end.strftime('%Y-%m-%d')

    rows = db.execute('SELECT price, qty, date FROM expenses').fetchall()
    df   = rows_to_df(rows)

    if df.empty:
        return {
            'budget': budget, 'spent': 0, 'spent_prev': 0,
            'pct_change': 0, 'remaining': budget,
            'budget_pct': 0, 'savings': 0, 'total_purchases': 0
        }

    df['total'] = df['price'] * df['qty']
    df['date']  = pd.to_datetime(df['date'])

    spent       = df[df['date'] >= start]['total'].sum()
    spent_prev  = df[(df['date'] >= prev_start) & (df['date'] <= prev_end)]['total'].sum()
    total_purch = df[df['date'] >= start].shape[0]

    pct_change = 0
    if spent_prev > 0:
        pct_change = round(((spent - spent_prev) / spent_prev) * 100, 1)

    remaining  = budget - spent
    budget_pct = min(round((spent / budget) * 100, 1), 100) if budget > 0 else 0
    savings    = _calc_potential_savings(db)

    return {
        'budget':          round(budget, 2),
        'spent':           round(spent, 2),
        'spent_prev':      round(spent_prev, 2),
        'pct_change':      pct_change,
        'remaining':       round(remaining, 2),
        'budget_pct':      budget_pct,
        'savings':         round(savings, 2),
        'total_purchases': total_purch,
    }


def _calc_potential_savings(db) -> float:
    """Calculate total potential savings by comparing last paid vs minimum prices.

    Compares the most recent price paid for each product against the
    historically lowest price recorded across all stores.

    Args:
        db: Active SQLite database connection (flask.g.db).

    Returns:
        float: Sum of overpayments compared to minimum recorded prices.
    """
    rows = db.execute(
        'SELECT name, price, store FROM expenses WHERE store != ""'
    ).fetchall()
    df = rows_to_df(rows)
    if df.empty:
        return 0.0
    min_prices  = df.groupby('name')['price'].min()
    last_prices = df.groupby('name')['price'].last()
    return float((last_prices - min_prices).clip(lower=0).sum())
