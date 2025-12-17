from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from config import config
from models import db, User
import os

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize extensions
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register blueprints
from routes.auth import auth_bp
from routes.household import household_bp
from routes.food import food_bp
from routes.consumption import consumption_bp
from routes.prediction import prediction_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(household_bp, url_prefix='/household')
app.register_blueprint(food_bp, url_prefix='/food')
app.register_blueprint(consumption_bp, url_prefix='/consumption')
app.register_blueprint(prediction_bp, url_prefix='/prediction')


# Main routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('prediction.dashboard'))
    return redirect(url_for('auth.login'))


@app.route('/about')
def about():
    return render_template('about.html')


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# Context processors
@app.context_processor
def inject_app_info():
    return {
        'app_name': app.config['APP_NAME'],
        'app_version': app.config['APP_VERSION']
    }


# Create database tables
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)