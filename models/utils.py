from datetime import datetime
import pandas as pd

def rows_to_df(rows) -> pd.DataFrame:
    """Convert a list of sqlite3.Row objects to a pandas DataFrame."""
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def current_month_bounds():
    """Return (start_date, end_date) strings for the current month."""
    now   = datetime.now()
    start = now.replace(day=1).strftime('%Y-%m-%d')
    end   = now.strftime('%Y-%m-%d')
    return start, end


def month_short(m: int) -> str:
    """Return a short Ukrainian month name for month number m (1–12)."""
    names = ['', 'Січ', 'Лют', 'Бер', 'Квіт', 'Трав', 'Черв',
             'Лип', 'Серп', 'Вер', 'Жовт', 'Лист', 'Груд']
    return names[m]


def get_budget(db) -> float:
    """Return the user's monthly budget, defaulting to 14000.0 if not set."""
    user = db.execute('SELECT budget FROM users WHERE id=1').fetchone()
    return float(user['budget']) if user else 14000.0
