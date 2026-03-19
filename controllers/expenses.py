import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from datetime import datetime

bp = Blueprint('expenses', __name__, url_prefix='/expenses')

_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

@bp.route('/')
def index():
    db       = get_db()
    category = request.args.get('category', '')
    query, params = 'SELECT * FROM expenses', []
    if category:
        query += ' WHERE category = ?'
        params.append(category)
    query += ' ORDER BY date DESC'
    return render_template('expenses.html',
                           expenses=db.execute(query, params).fetchall(),
                           cats=db.execute('SELECT DISTINCT category FROM expenses ORDER BY category').fetchall(),
                           selected_cat=category,
                           today=datetime.now().strftime('%Y-%m-%d'))

@bp.route('/add', methods=['POST'])
def add():
    name     = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    price    = request.form.get('price', '').strip()
    store    = request.form.get('store', '').strip()
    date     = request.form.get('date', '').strip()
    qty      = request.form.get('qty', '1').strip()

    # Серверна валідація
    if not name or len(name) > 200:
        flash('Назва товару обов\'язкова (до 200 символів)!', 'danger')
        return redirect(url_for('expenses.index'))
    if not _DATE_RE.match(date):
        flash('Невірний формат дати!', 'danger')
        return redirect(url_for('expenses.index'))

    try:
        price_val = float(price)
        qty_val   = max(int(qty), 1)
        if price_val <= 0:
            raise ValueError
    except ValueError:
        flash('Невірний формат ціни або кількості!', 'danger')
        return redirect(url_for('expenses.index'))

    db = get_db()
    db.execute(
        'INSERT INTO expenses (name, category, price, store, date, qty) VALUES (?,?,?,?,?,?)',
        (name, category, price_val, store, date, qty_val)
    )
    db.commit()
    flash(f'Покупку «{name}» успішно додано!', 'success')
    return redirect(url_for('expenses.index'))

@bp.route('/delete/<int:expense_id>', methods=['POST'])
def delete(expense_id):
    db = get_db()
    db.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    db.commit()
    flash('Запис видалено.', 'info')
    return redirect(url_for('expenses.index'))