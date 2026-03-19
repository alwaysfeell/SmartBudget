from datetime import datetime, timedelta
import pandas as pd
from models.utils import rows_to_df, month_short, get_budget

_SEASONAL = {1: -0.02, 2: -0.05, 3: 0.00, 4: 0.03, 5: 0.05,
             6: 0.04,  7: 0.02,  8: 0.01, 9: 0.02, 10: 0.03,
             11: 0.05, 12: 0.12}

def get_forecast(db) -> dict:
    rows = db.execute('SELECT price, qty, date, category FROM expenses').fetchall()
    df   = rows_to_df(rows)
    now  = datetime.now()

    month_totals, month_labels, months_list = {}, [], []
    for i in range(5, -1, -1):
        d   = now.replace(day=1) - timedelta(days=i * 28)
        key = (d.year, d.month)
        months_list.append(key)
        month_labels.append(f'{month_short(d.month)} {d.year}')
        month_totals[key] = 0.0

    if not df.empty:
        df['total'] = df['price'] * df['qty']
        df['date']  = pd.to_datetime(df['date'])
        for (y, m), grp in df.groupby([df['date'].dt.year, df['date'].dt.month]):
            if (y, m) in month_totals:
                month_totals[(y, m)] = float(grp['total'].sum())

    history  = [month_totals[k] for k in months_list]
    non_zero = [(i, v) for i, v in enumerate(history) if v > 0]

    if len(non_zero) >= 2:
        xs, ys   = [p[0] for p in non_zero], [p[1] for p in non_zero]
        n        = len(xs)
        mean_x, mean_y = sum(xs) / n, sum(ys) / n
        num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
        den = sum((xs[i] - mean_x) ** 2 for i in range(n))
        slope     = num / den if den != 0 else 0
        intercept = mean_y - slope * mean_x
        residuals = [ys[i] - (intercept + slope * xs[i]) for i in range(n)]
        std_res   = (sum(r**2 for r in residuals) / max(n - 1, 1)) ** 0.5
    else:
        avg       = sum(history) / max(len([v for v in history if v > 0]), 1)
        slope, intercept, std_res = 0, avg, avg * 0.1

    forecast_labels, forecast_values, forecast_low, forecast_high = [], [], [], []
    for i in range(1, 4):
        offset    = now.month - 1 + i
        fut_year  = now.year + offset // 12
        fut_month = offset % 12 + 1
        base      = intercept + slope * (5 + i)
        predicted = max(base * (1 + _SEASONAL.get(fut_month, 0)), 0)
        forecast_labels.append(f'{month_short(fut_month)} {fut_year}')
        forecast_values.append(round(predicted, 2))
        forecast_low.append(round(max(predicted - std_res, 0), 2))
        forecast_high.append(round(predicted + std_res, 2))

    cat_forecast = []
    if not df.empty:
        months_count = max(len([v for v in history if v > 0]), 1)
        for cat, avg in (df.groupby('category')['total'].sum() / months_count).nlargest(3).items():
            cat_forecast.append({
                'category':    cat,
                'avg_monthly': round(float(avg), 2),
                'next_month':  round(float(avg) * (1 + _SEASONAL.get(now.month % 12 + 1, 0)), 2),
            })

    budget    = get_budget(db)
    next_pred = forecast_values[0] if forecast_values else 0
    risk_pct  = round((next_pred / budget) * 100, 1) if budget > 0 else 0
    if risk_pct > 100:
        risk_level = 'high'
        risk_text  = f'Прогноз ({next_pred:.0f} ₴) перевищує бюджет ({budget:.0f} ₴) на {next_pred - budget:.0f} ₴'
    elif risk_pct > 85:
        risk_level = 'medium'
        risk_text  = f'Прогноз ({next_pred:.0f} ₴) близький до бюджету, залишок лише {budget - next_pred:.0f} ₴'
    else:
        risk_level = 'low'
        risk_text  = f'Прогноз ({next_pred:.0f} ₴) в межах бюджету ({budget:.0f} ₴), запас {budget - next_pred:.0f} ₴'

    return {
        'history_labels':  month_labels,
        'history_values':  history,
        'forecast_labels': forecast_labels,
        'forecast_values': forecast_values,
        'forecast_low':    forecast_low,
        'forecast_high':   forecast_high,
        'cat_forecast':    cat_forecast,
        'risk_level':      risk_level,
        'risk_text':       risk_text,
        'risk_pct':        risk_pct,
        'slope':           round(slope, 2),
        'trend_direction': 'up' if slope > 50 else 'down' if slope < -50 else 'stable',
    }