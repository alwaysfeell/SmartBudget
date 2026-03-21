from datetime import datetime
import pandas as pd
from models.utils import rows_to_df, get_budget

_NEEDS_CATS = {'Продукти', 'Транспорт', 'Комунальні', 'Медицина', 'Побутова хімія', 'Гігієна'}
_WANTS_CATS = {'Одяг та взуття', 'Розваги', 'Кафе та ресторани', 'Хобі', 'Краса'}
_SAVES_CATS = {'Заощадження', 'Інвестиції', 'Погашення боргу'}

def get_budget_rule_503020(db) -> dict:
    """Analyse spending against the 50/30/20 budget rule and return category breakdown.

    Classifies every expense category into one of three buckets:
        - Needs (50% target): essentials such as groceries, transport, utilities.
        - Wants (30% target): discretionary spending such as dining out, hobbies.
        - Saves (20% target): savings, investments, debt repayment.
    Unrecognised categories are counted as Needs.

    Args:
        db: Active SQLite database connection (flask.g.db).

    Returns:
        dict: Keys include budget, total_spent, needs, wants, saves,
              needs_pct, wants_pct, saves_pct, target_needs, target_wants,
              target_saves, needs_delta, wants_delta, saves_delta,
              needs_status, wants_status, saves_status (ok/over/under),
              cat_breakdown, top_needs, top_wants, unclassified, tips,
              recommended_save.
    """
    rows   = db.execute('SELECT category, price, qty, date FROM expenses').fetchall()
    df     = rows_to_df(rows)
    budget = get_budget(db)

    tn, tw, ts = round(budget * .50, 2), round(budget * .30, 2), round(budget * .20, 2)

    if df.empty:
        return _empty(budget, tn, tw, ts)

    df['total'] = df['price'] * df['qty']
    df['date']  = pd.to_datetime(df['date'])
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    month_df    = df[df['date'] >= month_start]
    if month_df.empty:
        month_df = df

    needs, wants, saves = 0.0, 0.0, 0.0
    unclassified, cat_breakdown = {}, {}

    for cat, grp in month_df.groupby('category'):
        total = float(grp['total'].sum())
        cat_breakdown[cat] = round(total, 2)
        if cat in _NEEDS_CATS:         needs += total
        elif cat in _WANTS_CATS:       wants += total
        elif cat in _SAVES_CATS:       saves += total
        else:
            needs += total
            unclassified[cat] = round(total, 2)

    total_spent = needs + wants + saves

    def pct(v):  return round(v / total_spent * 100, 1) if total_spent > 0 else 0
    def status(delta, tol=500): return 'over' if delta > tol else 'under' if delta < -tol else 'ok'

    nd, wd, sd = round(needs - tn, 2), round(wants - tw, 2), round(saves - ts, 2)
    ns, ws, ss = status(nd), status(wd), status(sd, 200)

    top_needs = sorted(
        [(c, v) for c, v in cat_breakdown.items() if c in _NEEDS_CATS | set(unclassified)],
                       key=lambda x: x[1], reverse=True)[:3]
    top_wants = sorted([(c, v) for c, v in cat_breakdown.items() if c in _WANTS_CATS],
                       key=lambda x: x[1], reverse=True)[:3]

    tips = []
    if ns == 'over':
        cats_str = ', '.join(f'«{c}»' for c, _ in top_needs[:2])
        tips.append({
            'type': 'needs', 'icon': 'bi-exclamation-triangle', 'color': 'amber',
            'text': (
                f'Необхідні витрати перевищують норму на {abs(nd):.0f} ₴. '
                f'Найбільші статті: {cats_str}.'
                f' Оптимізуйте покупки через порівняння цін.'
            ),
        })
    if ws == 'over':
        cats_str = ', '.join(f'«{c}»' for c, _ in top_wants[:2]) if top_wants else 'розваги'
        tips.append({
            'type': 'wants', 'icon': 'bi-cart-x', 'color': 'red',
            'text': (
                f'Бажані витрати на {abs(wd):.0f} ₴ більше норми (30%). '
                f'Категорії: {cats_str}.'
                f' Скорочення дасть +{abs(wd):.0f} ₴ на заощадження.'
            ),
        })
    if ss == 'under':
        tips.append({
            'type': 'saves', 'icon': 'bi-piggy-bank', 'color': 'blue',
            'text': (
                f'Заощадження ({saves:.0f} ₴) нижче цілі {ts:.0f} ₴'
                f' на {abs(sd):.0f} ₴. Навіть відкладаючи'
                f' {abs(sd)/12:.0f} ₴ щотижня — ціль буде досягнута.'
            ),
        })
    if not tips:
        tips.append({'type': 'ok', 'icon': 'bi-check-circle', 'color': 'green',
                     'text': 'Чудово! Ваші витрати близькі до правила 50/30/20.'})

    return {
        'budget': budget, 'total_spent': round(total_spent, 2),
        'needs': round(needs, 2), 'wants': round(wants, 2), 'saves': round(saves, 2),
        'needs_pct': pct(needs), 'wants_pct': pct(wants), 'saves_pct': pct(saves),
        'target_needs': tn, 'target_wants': tw, 'target_saves': ts,
        'needs_delta': nd, 'wants_delta': wd, 'saves_delta': sd,
        'needs_status': ns, 'wants_status': ws, 'saves_status': ss,
        'cat_breakdown': cat_breakdown, 'top_needs': top_needs, 'top_wants': top_wants,
        'unclassified': unclassified, 'tips': tips,
        'recommended_save': max(round(budget * .20, 2) - saves, 0),
    }


def _empty(budget, tn, tw, ts):
    """Return a zeroed-out result dict when there are no expense records.

    Args:
        budget: Monthly budget amount.
        tn: Target amount for needs (50% of budget).
        tw: Target amount for wants (30% of budget).
        ts: Target amount for saves (20% of budget).

    Returns:
        dict: Same structure as get_budget_rule_503020 but all values are zero.
    """
    return {
        'budget': budget, 'total_spent': 0,
        'needs': 0, 'wants': 0, 'saves': 0,
        'needs_pct': 0, 'wants_pct': 0, 'saves_pct': 0,
        'target_needs': tn, 'target_wants': tw, 'target_saves': ts,
        'needs_delta': -tn, 'wants_delta': -tw, 'saves_delta': -ts,
        'needs_status': 'under', 'wants_status': 'under', 'saves_status': 'under',
        'cat_breakdown': {}, 'top_needs': [], 'top_wants': [],
        'unclassified': {}, 'tips': [], 'recommended_save': ts,
    }
