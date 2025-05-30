from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from app.config.config import config
from app.models.models import db
from app.services.sms_service import sms_service
from app.services.ai_service import ai_service

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize database
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Initialize services
    with app.app_context():
        sms_service.initialize()
        ai_service.initialize()
    
    # Register blueprints
    from app.routes.sms_routes import sms_bp
    from app.routes.web_routes import web_bp
    from app.routes.health_routes import health_bp
    
    app.register_blueprint(sms_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(health_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app 