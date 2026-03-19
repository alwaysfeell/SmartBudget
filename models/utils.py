from datetime import datetime, timedelta
import pandas as pd

def rows_to_df(rows) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def current_month_bounds():
    now   = datetime.now()
    start = now.replace(day=1).strftime('%Y-%m-%d')
    end   = now.strftime('%Y-%m-%d')
    return start, end


def month_short(m: int) -> str:
    names = ['', 'Січ', 'Лют', 'Бер', 'Квіт', 'Трав', 'Черв',
             'Лип', 'Серп', 'Вер', 'Жовт', 'Лист', 'Груд']
    return names[m]


def get_budget(db) -> float:
    user = db.execute('SELECT budget FROM users WHERE id=1').fetchone()
    return float(user['budget']) if user else 14000.0