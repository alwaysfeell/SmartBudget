from flask import Flask, g
from config import SECRET_KEY, DEBUG
from database import init_db

app = Flask(__name__)
app.secret_key = SECRET_KEY

with app.app_context():
    init_db()

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

from controllers.main            import bp as main_bp
from controllers.expenses        import bp as expenses_bp
from controllers.analysis        import bp as analysis_bp
from controllers.recommendations import bp as recs_bp
from controllers.dss             import bp as dss_bp
from controllers.profile         import bp as profile_bp
from controllers.goals           import bp as goals_bp

app.register_blueprint(main_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(recs_bp)
app.register_blueprint(dss_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(goals_bp)

if __name__ == '__main__':
    app.run(debug=DEBUG, port=5000)