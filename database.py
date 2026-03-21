import sqlite3
from flask import g

DATABASE = 'smartbudget.db'


def get_db():
    """Return the current database connection, creating it if necessary.

    Uses Flask application context (flask.g) to store one connection
    per HTTP request (connection-per-request pattern). The connection
    is automatically closed when the application context tears down.

    Returns:
        sqlite3.Connection: Open connection with Row factory enabled,
            allowing column access by name (row['column']).
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    """Initialise the SQLite schema and seed demo data if the database is empty.

    Creates the following tables if they do not exist:
        - expenses: individual purchase records.
        - users: single-user profile with budget settings.
        - stores: store name reference list.
        - goals: savings goals with progress tracking.

    Also inserts a default user record (id=1) and demo expense data
    so the dashboard is not empty on first run.
    """
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE IF NOT EXISTS expenses (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            category   TEXT    NOT NULL DEFAULT '',
            price      REAL    NOT NULL,
            store      TEXT    NOT NULL DEFAULT '',
            date       TEXT    NOT NULL,
            qty        INTEGER NOT NULL DEFAULT 1,
            created_at TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY DEFAULT 1,
            first_name TEXT DEFAULT 'Владислав',
            last_name  TEXT DEFAULT 'Косілов',
            email      TEXT DEFAULT 'kosin24@example.com',
            city       TEXT DEFAULT 'Київ',
            budget     REAL DEFAULT 14000.0,
            currency   TEXT DEFAULT '₴',
            registered TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS stores (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS goals (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT    NOT NULL,
            target_amount REAL    NOT NULL,
            saved_amount  REAL    NOT NULL DEFAULT 0,
            monthly_save  REAL    NOT NULL DEFAULT 0,
            deadline      TEXT    DEFAULT '',
            category      TEXT    NOT NULL DEFAULT 'Інше',
            icon          TEXT    NOT NULL DEFAULT '🎯',
            color         TEXT    NOT NULL DEFAULT '#2563eb',
            created_at    TEXT    DEFAULT (date('now'))
        );
    ''')
