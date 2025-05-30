import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///sms_learning.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Africa's Talking settings
    AT_USERNAME = os.getenv('AT_USERNAME')
    AT_API_KEY = os.getenv('AT_API_KEY')
    
    # Gemini AI settings
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Session settings
    SESSION_LIFETIME = 3600  # 1 hour in seconds
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 