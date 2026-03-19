import math
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import get_db
from models.stats import get_stats

bp = Blueprint('goals', __name__, url_prefix='/goals')

_MONTH_NAMES = ['Січень','Лютий','Березень','Квітень','Травень','Червень',
                'Липень','Серпень','Вересень','Жовтень','Листопад','Грудень']

@bp.route('/')
def index():
    db        = get_db()
    raw_stats = get_stats(db)
    return render_template('goals.html',
                           goals=db.execute('SELECT * FROM goals ORDER BY created_at DESC').fetchall(),
                           stats={k: float(v) if hasattr(v, 'item') else v for k, v in raw_stats.items()},
                           today=datetime.now().strftime('%Y-%m-%d'))


@bp.route('/add', methods=['POST'])
def add():
    title = request.form.get('title', '').strip()
    if not title:
        flash('Введіть назву цілі!', 'danger')
        return redirect(url_for('goals.index'))
    try:
        target  = float(request.form.get('target_amount', '0'))
        saved   = float(request.form.get('saved_amount',  '0'))
        monthly = float(request.form.get('monthly_save',  '0'))
        if target <= 0:
            raise ValueError
    except ValueError:
        flash('Невірний формат суми!', 'danger')
        return redirect(url_for('goals.index'))

    db = get_db()
    db.execute(
        'INSERT INTO goals (title, target_amount, saved_amount, monthly_save, deadline, category, icon, color) '
        'VALUES (?,?,?,?,?,?,?,?)',
        (title, target, saved, monthly,
         request.form.get('deadline', '').strip(),
         request.form.get('category', 'Інше').strip(),
         request.form.get('icon', 'target').strip(),
         request.form.get('color', '#2563eb').strip())
    )
    db.commit()
    flash(f'Ціль «{title}» додано!', 'success')
    return redirect(url_for('goals.index'))


@bp.route('/deposit/<int:goal_id>', methods=['POST'])
def deposit(goal_id):
    try:
        amount = float(request.form.get('amount', '0'))
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash('Невірна сума!', 'danger')
        return redirect(url_for('goals.index'))
    db = get_db()
    db.execute('UPDATE goals SET saved_amount = saved_amount + ? WHERE id = ?', (amount, goal_id))
    db.commit()
    flash(f'+{amount:,.0f} грн зараховано до цілі!', 'success')
    return redirect(url_for('goals.index'))


@bp.route('/delete/<int:goal_id>', methods=['POST'])
def delete(goal_id):
    db = get_db()
    db.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
    db.commit()
    flash('Ціль видалено.', 'info')
    return redirect(url_for('goals.index'))


@bp.route('/calc', methods=['POST'])
def calc():
    data = request.get_json(force=True)
    try:
        target  = float(data.get('target',  0))
        saved   = float(data.get('saved',   0))
        monthly = float(data.get('monthly', 0))
        months  = float(data.get('months',  0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Невірні дані'}), 400

    remaining = max(target - saved, 0)
    if monthly > 0:
        months_needed, monthly_needed = remaining / monthly, monthly
    elif months > 0:
        monthly_needed, months_needed = remaining / months, months
    else:
        return jsonify({'error': 'Введіть місячний внесок або строк'}), 400

    m     = int(math.ceil(months_needed))
    today = date.today()
    year  = today.year + (today.month - 1 + m) // 12
    month = (today.month - 1 + m) % 12 + 1

    return jsonify({
        'remaining':      round(remaining, 2),
        'monthly_needed': round(monthly_needed, 2),
        'months_needed':  round(months_needed, 1),
        'finish_date':    f'{_MONTH_NAMES[month - 1]} {year}',
        'progress':       round(saved / target * 100, 1) if target > 0 else 0,
    })