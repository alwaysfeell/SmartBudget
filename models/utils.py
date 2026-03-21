from datetime import datetime
import pandas as pd


def rows_to_df(rows) -> pd.DataFrame:
    """Convert a list of sqlite3.Row objects to a pandas DataFrame.

    Args:
        rows: List of sqlite3.Row objects returned by db.execute().fetchall().

    Returns:
        pd.DataFrame: DataFrame with column names matching the SQL query,
            or an empty DataFrame if rows is empty.
    """
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def current_month_bounds():
    """Return start and end date strings for the current calendar month.

    Returns:
        tuple[str, str]: (start_date, end_date) in 'YYYY-MM-DD' format,
            where start_date is the first day of the current month
            and end_date is today.
    """
    now   = datetime.now()
    start = now.replace(day=1).strftime('%Y-%m-%d')
    end   = now.strftime('%Y-%m-%d')
    return start, end


def month_short(m: int) -> str:
    """Return a short Ukrainian month name for the given month number.

    Args:
        m (int): Month number from 1 (January) to 12 (December).

    Returns:
        str: Short Ukrainian month abbreviation, e.g. 'Січ', 'Лют', 'Бер'.
    """
    names = ['', 'Січ', 'Лют', 'Бер', 'Квіт', 'Трав', 'Черв',
             'Лип', 'Серп', 'Вер', 'Жовт', 'Лист', 'Груд']
    return names[m]


def get_budget(db) -> float:
    """Return the user's monthly budget from the database.

    Reads the budget field from the users table for user id=1.
    Falls back to 14000.0 if no user record exists.

    Args:
        db: Active SQLite database connection (flask.g.db).

    Returns:
        float: Monthly budget amount in UAH.
    """
    user = db.execute('SELECT budget FROM users WHERE id=1').fetchone()
    return float(user['budget']) if user else 14000.0
