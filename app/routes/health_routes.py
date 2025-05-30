from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
from app.models.models import db
from app.services.sms_service import sms_service
from app.services.ai_service import ai_service

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint."""
    at_status = sms_service.initialized
    gemini_status = ai_service.initialized
    
    # Test database connection
    try:
        db.session.execute('SELECT 1')
        db_status = True
    except:
        db_status = False
    
    # Test Africa's Talking credentials
    try:
        if sms_service.initialized:
            at_detailed = "Initialized"
        else:
            at_detailed = "Not initialized"
    except:
        at_detailed = "Error"
    
    return jsonify({
        "status": "healthy" if all([at_status, gemini_status, db_status]) else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "sms": {
                "status": at_status,
                "details": at_detailed
            },
            "ai": {
                "status": gemini_status,
                "model": "gemini-2.0-flash" if gemini_status else None
            },
            "database": {
                "status": db_status
            }
        },
        "config": {
            "at_username": request.host_url + 'sms_callback'
        }
    }) 