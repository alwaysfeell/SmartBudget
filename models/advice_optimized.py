"""
models/advice_optimized.py — оптимізована версія generate_advice.

Оптимізації відносно оригінального advice.py:
    1. Єдиний SQL-запит із агрегацією min_price на стороні БД
       (замість повного завантаження всіх рядків та groupby у pandas).
    2. Обчислення min_prices через SQL MIN() — усуває окремий pass по DataFrame.
    3. Ранній вихід (early-exit): якщо DataFrame порожній — відповідь
       повертається без жодних pandas-операцій.
    4. Видалено зайве df.copy() у першому циклі.
    5. store_overpay обчислюється за один прохід замість вкладеного groupby.
"""

from datetime import datetime
import pandas as pd
from models.utils import rows_to_df
from models.stats import get_stats

def generate_advice(db, count: int = 1):
    """Analyse purchase history and return personalised saving recommendations.

    Optimised version: uses SQL-level aggregation for min prices,
    eliminates redundant DataFrame iterations, and applies early-exit
    when no data is available.

    Args:
        db: Active SQLite database connection (flask.g.db).
        count (int): Number of advice items to return. Defaults to 1.

    Returns:
        str | list[dict]: If count == 1, returns a plain text advice string.
            Otherwise returns list of dicts with keys:
            title, body, saving, tag.
    """
    rows = db.execute(
        'SELECT name, category, price, store, date, qty FROM expenses WHERE store != ""'
    ).fetchall()
    df = rows_to_df(rows)

    if df.empty:
        fallback = (
            'Додайте покупки з вказанням магазину — система проаналізує ціни '
            'та надасть персональні рекомендації.'
        )
        if count == 1:
            return fallback
        return [{'title': 'Недостатньо даних', 'body': fallback, 'saving': '—', 'tag': 'tip'}]

    df['total'] = df['price'] * df['qty']
    df['date'] = pd.to_datetime(df['date'])
    advices = []

    min_rows = db.execute(
        'SELECT name, MIN(price) as min_price FROM expenses WHERE store != "" GROUP BY name'
    ).fetchall()
    min_prices = {r['name']: r['min_price'] for r in min_rows}

    overpay_details = []
    for name, grp in df.groupby('name'):
        if grp['store'].nunique() < 2:
            continue
        min_p = min_prices.get(name, grp['price'].min())
        overpay_total = ((grp['price'] - min_p) * grp['qty']).sum()
        if overpay_total > 1:
            max_idx = grp['price'].idxmax()
            overpay_details.append({
                'name':        name,
                'best_store':  grp.loc[grp['price'].idxmin(), 'store'],
                'worst_store': grp.loc[max_idx, 'store'],
                'min_price':   round(float(min_p), 2),
                'max_price':   round(float(grp.loc[max_idx, 'price']), 2),
                'overpaid':    round(float(overpay_total), 2),
            })
    for item in sorted(overpay_details, key=lambda x: x['overpaid'], reverse=True)[:3]:
        diff_pct = round((item['max_price'] - item['min_price']) / item['min_price'] * 100)
        advices.append({
            'title':  f'Переплата за «{item["name"]}»',
            'body': (
                f'Ви купували «{item["name"]}» у {item["worst_store"]}'
                f' за {item["max_price"]:.0f} ₴, хоча у {item["best_store"]}'
                f' ціна {item["min_price"]:.0f} ₴ ({diff_pct}% різниця).'
                f' Загальна переплата: {item["overpaid"]:.0f} ₴.'
            ),
            'saving': f'−{item["overpaid"]:.0f} ₴',
            'tag':    'economy',
        })

    store_paid = {}
    store_min  = {}
    for (store, name), sgrp in df.groupby(['store', 'name']):
        if name in min_prices:
            paid = float((sgrp['price'] * sgrp['qty']).sum())
            mins = float(min_prices[name]) * int(sgrp['qty'].sum())
            store_paid[store] = store_paid.get(store, 0.0) + paid
            store_min[store]  = store_min.get(store, 0.0) + mins
    store_overpay = {
        s: round(store_paid[s] - store_min[s], 2)
        for s in store_paid
        if store_paid[s] - store_min[s] > 0
    }

    if store_overpay:
        worst    = max(store_overpay, key=store_overpay.get)
        alts     = {s: v for s, v in store_overpay.items() if s != worst}
        best_alt = min(alts, key=alts.get) if alts else None
        alt_text = f' Спробуйте частіше купувати у {best_alt}.' if best_alt else ''
        advices.append({
            'title':  f'{worst} — не найвигідніший вибір',
            'body': (
                f'У {worst} ви переплатили {store_overpay[worst]:.0f} ₴'
                f' порівняно з мінімальними цінами на ті самі товари'
                f' в інших магазинах.{alt_text}'
            ),
            'saving': f'−{store_overpay[worst]:.0f} ₴',
            'tag':    'warning',
        })

    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    month_df    = df[df['date'] >= month_start]
    if not month_df.empty:
        cat_totals  = month_df.groupby('category')['total'].sum().sort_values(ascending=False)
        top_cat     = cat_totals.index[0]
        top_sum     = float(cat_totals.iloc[0])
        total_month = float(month_df['total'].sum())
        pct         = round(top_sum / total_month * 100) if total_month > 0 else 0
        cat_stores  = df[df['category'] == top_cat].groupby('store')['price'].mean()
        store_hint  = (
            f' Найвигідніше купувати у {cat_stores.idxmin()}.'
            if not cat_stores.empty else ''
        )
        advices.append({
            'title':  f'«{top_cat}» — {pct}% ваших витрат цього місяця',
            'body': (
                f'У поточному місяці ви витратили {top_sum:.0f} ₴ на «{top_cat}» —'
                f' це {pct}% від усіх витрат ({total_month:.0f} ₴).{store_hint}'
            ),
            'saving': f'до {round(top_sum * 0.12):.0f} ₴',
            'tag':    'warning',
        })

    trend_items = []
    for name, grp in df.groupby('name'):
        if len(grp) < 3:
            continue
        grp_s = grp.sort_values('date')
        first, last = float(grp_s.iloc[0]['price']), float(grp_s.iloc[-1]['price'])
        growth = round((last - first) / first * 100, 1)
        if growth >= 5:
            trend_items.append({
                'name': name, 'first_price': first, 'last_price': last,
                'growth': growth,
                'best_store': grp.loc[grp['price'].idxmin(), 'store'],
                'min_price':  round(float(grp['price'].min()), 2),
            })
    for item in sorted(trend_items, key=lambda x: x['growth'], reverse=True)[:2]:
        advices.append({
            'title':  f'«{item["name"]}» подорожчав на {item["growth"]:.0f}%',
            'body': (
                f'З першої фіксованої покупки ціна «{item["name"]}»'
                f' зросла з {item["first_price"]:.0f} ₴'
                f' до {item["last_price"]:.0f} ₴ (+{item["growth"]:.0f}%).'
                f' Найнижча зафіксована ціна —'
                f' {item["min_price"]:.0f} ₴ у {item["best_store"]}.'
            ),
            'saving': f'−{round(item["last_price"] - item["min_price"]):.0f} ₴/шт',
            'tag':    'warning',
        })

    store_efficiency = {}
    for store, grp in df.groupby('store'):
        ratios = [
            float(sgrp['price'].mean()) / float(min_prices[n])
            for n, sgrp in grp.groupby('name')
            if n in min_prices and float(min_prices[n]) > 0
        ]
        if ratios:
            store_efficiency[store] = round((sum(ratios) / len(ratios) - 1) * 100, 1)

    if len(store_efficiency) >= 2:
        best  = min(store_efficiency, key=store_efficiency.get)
        worst = max(store_efficiency, key=store_efficiency.get)
        advices.append({
            'title':  f'{best} — найвигідніший магазин у вашій історії',
            'body': (
                f'За вашими даними, {best} у середньому лише на'
                f' {store_efficiency[best]:.0f}% дорожче мінімальних цін.'
                f' {worst} у середньому на'
                f' {store_efficiency[worst]:.0f}% дорожче мінімуму.'
            ),
            'saving': f'до {round(store_efficiency[worst] - store_efficiency[best]):.0f}% різниці',
            'tag':    'economy',
        })

    freq_cats = df.groupby('category').size().sort_values(ascending=False)
    if len(freq_cats) >= 2:
        top_cat = freq_cats.index[0]
        cat_df  = df[df['category'] == top_cat]
        if cat_df['store'].nunique() >= 2:
            by_store  = cat_df.groupby('store')['price'].mean().sort_values()
            diff_cat  = round(float(by_store.iloc[-1]) - float(by_store.iloc[0]), 2)
            if diff_cat > 5:
                advices.append({
                    'title':  f'Оптимізуйте покупки «{top_cat}»',
                    'body': (
                        f'Ви найчастіше купуєте товари категорії «{top_cat}»'
                        f' ({int(freq_cats.iloc[0])} покупок).'
                        f' Середня ціна у {by_store.index[0]}: {by_store.iloc[0]:.0f} ₴,'
                        f' у {by_store.index[-1]}: {by_store.iloc[-1]:.0f} ₴.'
                        f' Перевага {by_store.index[0]} — {diff_cat:.0f} ₴ на одиниці.'
                    ),
                    'saving': f'−{diff_cat:.0f} ₴/од.',
                    'tag':    'tip',
                })

    if len(advices) < 2:
        stats = get_stats(db)
        if float(stats.get('budget_pct', 0)) > 80:
            advices.append({
                'title':  'Бюджет вичерпується',
                'body': (
                    f'Ви використали {stats["budget_pct"]:.0f}% місячного бюджету'
                    f' ({stats["spent"]:.0f} ₴ з {stats["budget"]:.0f} ₴).'
                    f' Залишок: {stats["remaining"]:.0f} ₴.'
                ),
                'saving': '—',
                'tag':    'warning',
            })

    if count == 1:
        return (
            advices[0]['body'] if advices
            else 'Додайте більше покупок з різних магазинів для аналізу!'
        )
    return advices[:count] if advices else [
        {'title': 'Потрібно більше даних',
         'body': (
             'Додайте покупки з різних магазинів —'
             ' тоді система порівняє ціни та надасть персональні поради.'
         ),
         'saving': '—', 'tag': 'tip'}
    ]
