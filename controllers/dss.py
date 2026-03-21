from flask import Blueprint, render_template
from database import get_db
from models.stats import get_stats
from models.dss.forecast import get_forecast
from models.dss.scenarios import get_scenario_analysis
from models.dss.budget_rule import get_budget_rule_503020
from models.dss.quality import get_advice_quality

bp = Blueprint('dss', __name__)


@bp.route('/dss')
def index():
    """Render the DSS (Decision Support System) dashboard.

    Aggregates data from all DSS modules: budget statistics, spending
    forecast, scenario analysis, 50/30/20 rule breakdown, and data
    quality score.

    Returns:
        flask.Response: Rendered dss.html template with all DSS data.
    """
    db        = get_db()
    raw_stats = get_stats(db)
    stats     = {k: float(v) if hasattr(v, 'item') else v for k, v in raw_stats.items()}
    return render_template('dss.html',
                           stats=stats,
                           forecast=get_forecast(db),
                           scenario=get_scenario_analysis(db),
                           rule5020=get_budget_rule_503020(db),
                           quality=get_advice_quality(db))
