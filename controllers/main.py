from flask import Blueprint, render_template, jsonify
from database import get_db
from models.stats import get_stats
from models.charts import get_weekly_chart_data, get_category_chart_data
from datetime import datetime

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Render the main dashboard with budget stats and charts.

    Fetches current month statistics, 5 most recent expenses,
    weekly spending chart data, and category breakdown chart data.

    Returns:
        flask.Response: Rendered index.html template.
    """
    db        = get_db()
    raw_stats = get_stats(db)
    stats     = {k: float(v) if hasattr(v, 'item') else v for k, v in raw_stats.items()}
    recent    = db.execute('SELECT * FROM expenses ORDER BY date DESC LIMIT 5').fetchall()
    return render_template('index.html',
                           stats=stats, recent=recent,
                           weekly_data=get_weekly_chart_data(db),
                           cat_data=get_category_chart_data(db),
                           now=datetime.now(),
                           today=datetime.now().strftime('%Y-%m-%d'))


@bp.route('/api/charts')
def api_charts():
    """Return chart data as JSON for AJAX dashboard updates.

    Returns:
        flask.Response: JSON with keys 'weekly' and 'categories',
            each containing data formatted for Chart.js.
    """
    db = get_db()
    return jsonify({
        'weekly':     get_weekly_chart_data(db),
        'categories': get_category_chart_data(db),
    })
