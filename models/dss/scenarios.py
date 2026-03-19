from datetime import datetime
import pandas as pd
from models.utils import rows_to_df, get_budget

def get_scenario_analysis(db) -> dict:
    rows = db.execute(
        'SELECT name, category, price, store, qty, date FROM expenses WHERE store != ""'
    ).fetchall()
    df     = rows_to_df(rows)
    budget = get_budget(db)

    if df.empty:
        return {'scenarios': [], 'actions': [], 'budget': budget}

    df['total'] = df['price'] * df['qty']
    df['date']  = pd.to_datetime(df['date'])

    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    month_df    = df[df['date'] >= month_start]
    base_spent  = float(month_df['total'].sum()) if not month_df.empty else float(df['total'].mean() * 20)
    min_prices  = df.groupby('name')['price'].min()

    opt_total, savings_by_item = 0.0, []
    source_df = month_df if not month_df.empty else df
    for name, grp in source_df.groupby('name'):
        min_p   = float(min_prices.get(name, grp['price'].min()))
        actual  = float((grp['price'] * grp['qty']).sum())
        optimal = min_p * int(grp['qty'].sum())
        opt_total += optimal
        if actual - optimal > 0.5:
            best_store = df[df['name'] == name].loc[df[df['name'] == name]['price'].idxmin(), 'store']
            savings_by_item.append({
                'name': name, 'saving': round(actual - optimal, 2),
                'store': best_store, 'min_p': round(min_p, 2),
            })
    savings_by_item.sort(key=lambda x: x['saving'], reverse=True)
    opt_spent  = opt_total if opt_total > 0 else base_spent * 0.87
    opt_saving = round(base_spent - opt_spent, 2)

    pess_spent  = round(base_spent * (1 + 0.0058 * 3), 2)
    pess_saving = round(budget - pess_spent, 2)

    actions = [
        {'action': f'Купуйте «{i["name"]}» у {i["store"]}', 'saving': i['saving'], 'min_p': i['min_p']}
        for i in savings_by_item[:4]
    ]
    store_overpay = {}
    for store, grp in df.groupby('store'):
        total_p = float((grp['price'] * grp['qty']).sum())
        total_m = sum(
            float(min_prices.get(n, grp[grp['name'] == n]['price'].min())) * int(grp[grp['name'] == n]['qty'].sum())
            for n in grp['name'].unique() if n in min_prices.index
        )
        if total_p - total_m > 0:
            store_overpay[store] = round(total_p - total_m, 2)

    if store_overpay:
        worst = max(store_overpay, key=store_overpay.get)
        best  = min(store_overpay, key=store_overpay.get)
        if worst != best:
            actions.append({
                'action': f'Замінити {worst} → {best} для регулярних покупок',
                'saving': store_overpay[worst] - store_overpay.get(best, 0),
                'min_p':  None,
            })

    return {
        'budget': budget,
        'scenarios': [
            {
                'id': 'A', 'label': 'Оптимістичний', 'tag': 'success', 'icon': 'bi-emoji-smile',
                'desc':          'Всі покупки за мінімальними цінами у найдешевших магазинах',
                'spent':         round(opt_spent, 2),
                'saving':        opt_saving,
                'remaining':     round(budget - opt_spent, 2),
                'annual_effect': round(opt_saving * 12, 2),
            },
            {
                'id': 'B', 'label': 'Базовий', 'tag': 'primary', 'icon': 'bi-dash-circle',
                'desc':          'Поточна поведінка без змін у звичках',
                'spent':         round(base_spent, 2),
                'saving':        round(budget - base_spent, 2),
                'remaining':     round(budget - base_spent, 2),
                'annual_effect': 0,
            },
            {
                'id': 'C', 'label': 'Песимістичний', 'tag': 'danger', 'icon': 'bi-emoji-frown',
                'desc':          'Ціни зростають +7%/рік (прогноз інфляції 2026), без оптимізації',
                'spent':         pess_spent,
                'saving':        pess_saving,
                'remaining':     round(budget - pess_spent, 2),
                'annual_effect': round((pess_spent - base_spent) * 12, 2),
            },
        ],
        'actions':       actions[:5],
        'top_savings':   savings_by_item[:5],
        'potential_opt': round(opt_saving, 2),
    }