from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from models.stats import get_stats

bp = Blueprint('profile', __name__)


@bp.route('/profile')
def index():
    """Render the user profile page with current settings and statistics.

    Returns:
        flask.Response: Rendered profile.html template with user record
            and current month budget statistics.
    """
    db        = get_db()
    raw_stats = get_stats(db)
    return render_template('profile.html',
                           user=db.execute('SELECT * FROM users WHERE id = 1').fetchone(),
                           stats={
                               k: float(v) if hasattr(v, 'item') else v
                               for k, v in raw_stats.items()
                           })


@bp.route('/profile/update', methods=['POST'])
def update():
    """Handle profile update form submission.

    Validates that budget is a positive number, then updates the users
    table for id=1. Flashes success or error message.

    Returns:
        flask.Response: Redirect to profile.index.
    """
    first_name = request.form.get('first_name', '').strip()
    last_name  = request.form.get('last_name', '').strip()
    email      = request.form.get('email', '').strip()
    city       = request.form.get('city', '').strip()
    currency   = request.form.get('currency', '₴').strip()
    try:
        budget = float(request.form.get('budget', '14000'))
        if budget <= 0:
            raise ValueError
    except ValueError:
        flash('Невірне значення бюджету!', 'danger')
        return redirect(url_for('profile.index'))

    db = get_db()
    db.execute(
        'UPDATE users SET first_name=?, last_name=?, email=?,'
        ' city=?, budget=?, currency=? WHERE id=1',
        (first_name, last_name, email, city, budget, currency)
    )
    db.commit()
    flash('Профіль успішно оновлено!', 'success')
    return redirect(url_for('profile.index'))
