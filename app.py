import os
from flask import Flask, g, request, render_template_string

from config import SECRET_KEY, DEBUG
from database import init_db
from logger import setup_logging, get_logger, log_error

setup_logging()
logger = get_logger(__name__)

app = Flask(__name__)
app.secret_key = SECRET_KEY

with app.app_context():
    logger.info("Initialising database...")
    init_db()
    logger.info("Database ready.")

@app.before_request
def _log_request():
    """Логувати вхідний HTTP-запит."""
    logger.info(
        "REQUEST  %s %s | ip=%s",
        request.method, request.path, request.remote_addr,
    )

@app.after_request
def _log_response(response):
    """Логувати HTTP-відповідь."""
    logger.info("RESPONSE %s %s → %s", request.method, request.path, response.status_code)
    return response

@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of each request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
    if error:
        logger.error("Teardown error: %s", error)

_ERROR_HTML = """
<!DOCTYPE html><html lang="uk">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ code }} – {{ title }}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<style>body{background:#f8f9fa}.error-card{max-width:520px;margin:10vh auto}
.error-code{font-size:6rem;font-weight:700;color:#dc3545;line-height:1}</style>
</head><body>
<div class="error-card card shadow-sm p-5 text-center">
  <div class="error-code">{{ code }}</div>
  <h2 class="mt-3 mb-2">{{ title }}</h2>
  <p class="text-muted">{{ message }}</p>
  {% if error_id %}
  <p class="small text-secondary mt-3">
    Код помилки: <code>{{ error_id }}</code><br>
    <small>Вкажіть цей код при зверненні до підтримки.</small>
  </p>
  {% endif %}
  <div class="d-flex justify-content-center gap-3 mt-4">
    <a href="{{ action_url }}" class="btn btn-primary">{{ action }}</a>
    <a href="mailto:support@smartbudget.local" class="btn btn-outline-secondary">Повідомити про проблему</a>
  </div>
</div></body></html>
"""

def _render_error(code, title, message, action="На головну", action_url="/", error_id=None):
    return render_template_string(
        _ERROR_HTML,
        code=code, title=title, message=message,
        action=action, action_url=action_url, error_id=error_id,
    )

@app.errorhandler(404)
def not_found(exc):
    logger.warning("404 Not Found | path=%s | ip=%s", request.path, request.remote_addr)
    return _render_error(404, "Сторінку не знайдено",
        "Сторінка, яку ви шукаєте, не існує або була переміщена."), 404


@app.errorhandler(500)
def internal_error(exc):
    eid = log_error(logger, exc, context={"path": request.path, "ip": request.remote_addr})
    return _render_error(500, "Внутрішня помилка сервера",
        "На сервері сталася непередбачена помилка. Спробуйте пізніше або повідомте підтримку.",
        error_id=eid), 500


@app.errorhandler(403)
def forbidden(exc):
    logger.warning("403 Forbidden | path=%s | ip=%s", request.path, request.remote_addr)
    return _render_error(403, "Доступ заборонено",
        "У вас немає дозволу для доступу до цього ресурсу."), 403

from controllers.main            import bp as main_bp
from controllers.expenses        import bp as expenses_bp
from controllers.analysis        import bp as analysis_bp
from controllers.recommendations import bp as recs_bp
from controllers.dss             import bp as dss_bp
from controllers.profile         import bp as profile_bp
from controllers.goals           import bp as goals_bp

for bp in (main_bp, expenses_bp, analysis_bp, recs_bp, dss_bp, profile_bp, goals_bp):
    app.register_blueprint(bp)

logger.info("All blueprints registered. SmartBudget is ready.")

if __name__ == '__main__':
    logger.info("Starting SmartBudget dev server | debug=%s | port=5000", DEBUG)
    app.run(debug=DEBUG, port=5000)
    logger.info("SmartBudget dev server stopped.")