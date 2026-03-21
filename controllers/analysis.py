from flask import Blueprint, render_template, request, jsonify
from database import get_db
from models.prices import get_price_comparison
from models.advice import generate_advice

bp = Blueprint('analysis', __name__, url_prefix='/analysis')


@bp.route('/')
def index():
    """Render the price analysis page with optional store/category filter.

    Reads 'store' and 'category' query parameters and applies them
    as filters on the expenses table.

    Returns:
        flask.Response: Rendered analysis.html template with price
            comparison data and filtered expense records.
    """
    db           = get_db()
    sel_store    = request.args.get('store', '')
    sel_category = request.args.get('category', '')

    query, params = 'SELECT * FROM expenses WHERE 1=1', []
    if sel_store:
        query += ' AND store = ?'; params.append(sel_store)
    if sel_category:
        query += ' AND category = ?'; params.append(sel_category)
    query += ' ORDER BY name, price ASC'

    return render_template('analysis.html',
                           comparison=get_price_comparison(db),
                           filtered=db.execute(query, params).fetchall(),
                           stores=db.execute(
                               'SELECT DISTINCT store FROM expenses'
                               ' WHERE store != "" ORDER BY store'
                           ).fetchall(),
                           categories=db.execute(
                               'SELECT DISTINCT category FROM expenses ORDER BY category'
                           ).fetchall(),
                           sel_store=sel_store,
                           sel_category=sel_category)


@bp.route('/advice')
def advice():
    """Return a single saving advice tip as JSON for the dashboard widget.

    Returns:
        flask.Response: JSON with key 'advice' containing a plain text string.
    """
    return jsonify({'advice': generate_advice(get_db())})
