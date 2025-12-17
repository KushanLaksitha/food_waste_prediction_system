import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'root'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'food_waste_db'
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@'
        f'{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Waste risk thresholds
    HIGH_RISK_THRESHOLD = 70
    MEDIUM_RISK_THRESHOLD = 40
    LOW_RISK_THRESHOLD = 20
    
    # Alert settings
    DAYS_BEFORE_EXPIRY_ALERT = 3
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # File upload (if needed in future)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Application settings
    APP_NAME = 'Food Waste Prediction System'
    APP_VERSION = '1.0.0'


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    # In production, SECRET_KEY should be set via environment variable
    # The validation happens when the app is initialized, not at class definition


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}