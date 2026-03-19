from datetime import datetime
import pandas as pd
from models.utils import rows_to_df
from models.stats import get_stats

def generate_advice(db, count: int = 1):
    rows = db.execute(
        'SELECT name, category, price, store, date, qty FROM expenses WHERE store != ""'
    ).fetchall()
    df = rows_to_df(rows)

    if df.empty:
        fallback = 'Додайте покупки з вказанням магазину — система проаналізує ціни та надасть персональні рекомендації.'
        if count == 1:
            return fallback
        return [{'title': 'Недостатньо даних', 'body': fallback, 'saving': '—', 'tag': 'tip'}]

    df['total'] = df['price'] * df['qty']
    df['date']  = pd.to_datetime(df['date'])
    advices     = []
    min_prices  = df.groupby('name')['price'].min()

    overpay_details = []
    for name, grp in df.groupby('name'):
        if grp['store'].nunique() < 2:
            continue
        grp = grp.copy()
        grp['overpay'] = (grp['price'] - min_prices[name]) * grp['qty']
        total_overpay  = grp['overpay'].sum()
        if total_overpay > 1:
            worst_row = grp.loc[grp['price'].idxmax()]
            overpay_details.append({
                'name':        name,
                'best_store':  grp.loc[grp['price'].idxmin(), 'store'],
                'worst_store': worst_row['store'],
                'min_price':   round(float(min_prices[name]), 2),
                'max_price':   round(float(worst_row['price']), 2),
                'overpaid':    round(float(total_overpay), 2),
            })
    for item in sorted(overpay_details, key=lambda x: x['overpaid'], reverse=True)[:3]:
        diff_pct = round((item['max_price'] - item['min_price']) / item['min_price'] * 100)
        advices.append({
            'title':  f'Переплата за «{item["name"]}»',
            'body':   (f'Ви купували «{item["name"]}» у {item["worst_store"]} за {item["max_price"]:.0f} ₴, '
                       f'хоча у {item["best_store"]} ціна {item["min_price"]:.0f} ₴ ({diff_pct}% різниця). '
                       f'Загальна переплата: {item["overpaid"]:.0f} ₴.'),
            'saving': f'−{item["overpaid"]:.0f} ₴',
            'tag':    'economy',
        })

    store_overpay = {}
    for store, grp in df.groupby('store'):
        total_paid, total_min = 0.0, 0.0
        for name, sgrp in grp.groupby('name'):
            if name in min_prices.index:
                total_paid += float((sgrp['price'] * sgrp['qty']).sum())
                total_min  += float(min_prices[name]) * int(sgrp['qty'].sum())
        if total_paid - total_min > 0:
            store_overpay[store] = round(total_paid - total_min, 2)

    if store_overpay:
        worst = max(store_overpay, key=store_overpay.get)
        alts  = {s: v for s, v in store_overpay.items() if s != worst}
        best_alt  = min(alts, key=alts.get) if alts else None
        alt_text  = f' Спробуйте частіше купувати у {best_alt}.' if best_alt else ''
        advices.append({
            'title':  f'{worst} — не найвигідніший вибір',
            'body':   (f'У {worst} ви переплатили {store_overpay[worst]:.0f} ₴ '
                       f'порівняно з мінімальними цінами на ті самі товари в інших магазинах.{alt_text}'),
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
        store_hint  = f' Найвигідніше купувати у {cat_stores.idxmin()}.' if not cat_stores.empty else ''
        advices.append({
            'title':  f'«{top_cat}» — {pct}% ваших витрат цього місяця',
            'body':   (f'У поточному місяці ви витратили {top_sum:.0f} ₴ на «{top_cat}» — '
                       f'це {pct}% від усіх витрат ({total_month:.0f} ₴).{store_hint}'),
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
            'body':   (f'З першої фіксованої покупки ціна «{item["name"]}» '
                       f'зросла з {item["first_price"]:.0f} ₴ до {item["last_price"]:.0f} ₴ '
                       f'(+{item["growth"]:.0f}%). '
                       f'Найнижча зафіксована ціна — {item["min_price"]:.0f} ₴ у {item["best_store"]}.'),
            'saving': f'−{round(item["last_price"] - item["min_price"]):.0f} ₴/шт',
            'tag':    'warning',
        })

    store_efficiency = {}
    for store, grp in df.groupby('store'):
        ratios = [
            float(sgrp['price'].mean()) / float(min_prices[n])
            for n, sgrp in grp.groupby('name')
            if n in min_prices.index and float(min_prices[n]) > 0
        ]
        if ratios:
            store_efficiency[store] = round((sum(ratios) / len(ratios) - 1) * 100, 1)

    if len(store_efficiency) >= 2:
        best  = min(store_efficiency, key=store_efficiency.get)
        worst = max(store_efficiency, key=store_efficiency.get)
        advices.append({
            'title':  f'{best} — найвигідніший магазин у вашій історії',
            'body':   (f'За вашими даними, {best} у середньому лише на {store_efficiency[best]:.0f}% '
                       f'дорожче мінімальних цін. '
                       f'{worst} у середньому на {store_efficiency[worst]:.0f}% дорожче мінімуму.'),
            'saving': f'до {round(store_efficiency[worst] - store_efficiency[best]):.0f}% різниці',
            'tag':    'economy',
        })

    freq_cats = df.groupby('category').size().sort_values(ascending=False)
    if len(freq_cats) >= 2:
        top_cat = freq_cats.index[0]
        cat_df  = df[df['category'] == top_cat]
        if cat_df['store'].nunique() >= 2:
            by_store   = cat_df.groupby('store')['price'].mean().sort_values()
            diff_cat   = round(float(by_store.iloc[-1]) - float(by_store.iloc[0]), 2)
            if diff_cat > 5:
                advices.append({
                    'title':  f'Оптимізуйте покупки «{top_cat}»',
                    'body':   (f'Ви найчастіше купуєте товари категорії «{top_cat}» '
                               f'({int(freq_cats.iloc[0])} покупок). '
                               f'Середня ціна у {by_store.index[0]}: {by_store.iloc[0]:.0f} ₴, '
                               f'у {by_store.index[-1]}: {by_store.iloc[-1]:.0f} ₴. '
                               f'Перевага {by_store.index[0]} — {diff_cat:.0f} ₴ на одиниці товару.'),
                    'saving': f'−{diff_cat:.0f} ₴/од.',
                    'tag':    'tip',
                })

    if len(advices) < 2:
        stats = get_stats(db)
        if float(stats.get('budget_pct', 0)) > 80:
            advices.append({
                'title':  'Бюджет вичерпується',
                'body':   (f'Ви використали {stats["budget_pct"]:.0f}% місячного бюджету '
                           f'({stats["spent"]:.0f} ₴ з {stats["budget"]:.0f} ₴). '
                           f'Залишок: {stats["remaining"]:.0f} ₴.'),
                'saving': '—',
                'tag':    'warning',
            })

    if count == 1:
        return advices[0]['body'] if advices else 'Додайте більше покупок з різних магазинів для аналізу!'
    return advices[:count] if advices else [
        {'title': 'Потрібно більше даних',
         'body':  'Додайте покупки з різних магазинів — тоді система порівняє ціни та надасть персональні поради.',
         'saving': '—', 'tag': 'tip'}
    ]