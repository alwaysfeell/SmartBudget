import pandas as pd
from models.utils import rows_to_df

def get_advice_quality(db) -> dict:
    rows = db.execute('SELECT name, price, store, date, qty FROM expenses').fetchall()
    df   = rows_to_df(rows)

    if df.empty:
        return _empty()

    df['total'] = df['price'] * df['qty']
    df['date']  = pd.to_datetime(df['date'])

    total_items   = df['name'].nunique()
    total_stores  = df[df['store'] != '']['store'].nunique()
    total_records = len(df)

    multi_store   = df[df['store'] != ''].groupby('name')['store'].nunique()
    covered       = int((multi_store >= 2).sum())
    coverage_pct  = round(covered / total_items * 100) if total_items > 0 else 0
    diversity     = min(round(total_stores / 5 * 100), 100)

    date_range    = (df['date'].max() - df['date'].min()).days
    months_depth  = max(date_range / 30, 0)
    history_score = min(round(months_depth / 6 * 100), 100)

    min_prices = df[df['store'] != ''].groupby('name')['price'].min()
    opt, total_cmp = 0, 0
    for name, grp in df[df['store'] != ''].groupby('name'):
        if multi_store.get(name, 0) >= 2:
            min_p = float(min_prices[name])
            for _, row in grp.iterrows():
                total_cmp += 1
                if abs(float(row['price']) - min_p) < 0.01:
                    opt += 1
    saving_score = round(opt / total_cmp * 100) if total_cmp > 0 else 50
    trend_score  = min(round(total_records / 50 * 100), 100)

    overall = round(coverage_pct * .30 + diversity * .20 +
                    history_score * .20 + saving_score * .20 + trend_score * .10)

    if overall >= 80:   label, color, icon = 'Відмінно',       'green', 'bi-patch-check-fill'
    elif overall >= 60: label, color, icon = 'Добре',          'blue',  'bi-patch-check'
    elif overall >= 40: label, color, icon = 'Задовільно',     'amber', 'bi-exclamation-circle'
    else:               label, color, icon = 'Потребує даних', 'red',   'bi-x-circle'

    improvements = []
    if coverage_pct < 60:
        improvements.append({'metric': 'Охоплення цін', 'score': coverage_pct,
                              'hint': f'Додайте ціни для {total_items - covered} товарів у ≥2 магазинах.'})
    if total_stores < 4:
        improvements.append({'metric': 'Різноманіття магазинів', 'score': diversity,
                              'hint': f'Зараз {total_stores} магазини. Додайте ще {4 - total_stores} нових мереж.'})
    if months_depth < 3:
        improvements.append({'metric': 'Глибина історії', 'score': history_score,
                              'hint': f'Є дані за {months_depth:.0f} міс. Для прогнозу потрібно ≥3 місяці.'})
    if saving_score < 60:
        improvements.append({'metric': 'Реалізація заощаджень', 'score': saving_score,
                              'hint': f'{total_cmp - opt} з {total_cmp} покупок — не за мінімальною ціною.'})

    store_stats = sorted([
        {'store': s, 'records': len(g), 'items': g['name'].nunique(),
         'total': round(float(g['total'].sum()), 2)}
        for s, g in df[df['store'] != ''].groupby('store')
    ], key=lambda x: x['records'], reverse=True)

    return {
        'overall': overall, 'quality_label': label,
        'quality_color': color, 'quality_icon': icon,
        'coverage_pct': coverage_pct, 'diversity_score': diversity,
        'history_score': history_score, 'saving_score': saving_score,
        'trend_score': trend_score,
        'total_items': total_items, 'total_stores': total_stores,
        'total_records': total_records, 'covered_items': covered,
        'months_depth': round(months_depth, 1),
        'optimal_purchases': opt, 'total_comparable': total_cmp,
        'improvements': improvements, 'store_stats': store_stats[:6],
    }

def _empty():
    return {
        'overall': 0, 'quality_label': 'Немає даних',
        'quality_color': 'red', 'quality_icon': 'bi-x-circle',
        'coverage_pct': 0, 'diversity_score': 0, 'history_score': 0,
        'saving_score': 0, 'trend_score': 0,
        'total_items': 0, 'total_stores': 0, 'total_records': 0,
        'covered_items': 0, 'months_depth': 0,
        'optimal_purchases': 0, 'total_comparable': 0,
        'improvements': [], 'store_stats': [],
    }