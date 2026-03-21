from flask import Blueprint, render_template
from database import get_db
from models.stats import get_stats
from models.charts import get_savings_chart_data
from models.advice import generate_advice
from models.prices import get_price_comparison

bp = Blueprint('recommendations', __name__)


@bp.route('/recommendations')
def index():
    """Render the recommendations page with personalised saving advice.

    Fetches up to 5 advice items, savings trend chart data, and full
    price comparison table.

    Returns:
        flask.Response: Rendered recommendations.html template.
    """
    db        = get_db()
    raw_stats = get_stats(db)
    stats     = {k: float(v) if hasattr(v, 'item') else v for k, v in raw_stats.items()}
    return render_template('recommendations.html',
                           stats=stats,
                           savings=get_savings_chart_data(db),
                           recs=generate_advice(db, count=5),
                           overpay=get_price_comparison(db))
