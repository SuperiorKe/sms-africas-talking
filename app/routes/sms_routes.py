from flask import Blueprint, request, Response, jsonify
import logging
from datetime import datetime
from app.models.models import db, User, Message
from app.services.sms_service import sms_service
from app.services.ai_service import ai_service

sms_bp = Blueprint('sms', __name__)

@sms_bp.route('/sms_callback', methods=['POST'])
def sms_callback():
    """Handle incoming SMS messages from Africa's Talking webhook."""
    
    # Log raw request data for debugging
    logging.info(f"Raw SMS callback data: {request.form}")
    logging.info(f"Request headers: {dict(request.headers)}")
    
    # Validate request
    if not request.form:
        logging.error("Empty form data received")
        return Response("Bad Request", status=400)

    # Extract SMS data
    sender_phone = request.form.get('from')
    message_text = request.form.get('text', '').strip()
    link_id = request.form.get('linkId')
    date = request.form.get('date')
    to = request.form.get('to')  # Your shortcode
    
    logging.info(f"📱 SMS received:")
    logging.info(f"   From: {sender_phone}")
    logging.info(f"   To: {to}")
    logging.info(f"   Message: '{message_text}'")
    logging.info(f"   LinkID: {link_id}")
    logging.info(f"   Date: {date}")

    if not sender_phone or not message_text:
        logging.error("Missing sender phone or message text")
        return Response("Bad Request", status=400)

    try:
        # Get or create user
        user = User.query.filter_by(phone_number=sender_phone).first()
        if not user:
            user = User(phone_number=sender_phone)
            db.session.add(user)
            db.session.commit()
            logging.info(f"👤 New user created: {sender_phone}")

        # Save incoming message
        user_message = Message(
            user_id=user.id, 
            sender_type='user', 
            text=message_text,
            link_id=link_id
        )
        db.session.add(user_message)
        db.session.commit()
        logging.info(f"💾 User message saved to database")

        # Get conversation history
        conversation_history = Message.get_conversation_history(user.id)
        newline = '\n'
        logging.info(f"📚 Retrieved conversation history: {len(conversation_history.split(newline))} messages")
        
        # Generate AI response
        logging.info(f"🤖 Generating AI response...")
        ai_response = ai_service.generate_response(message_text, conversation_history)
        logging.info(f"🤖 AI Response generated: '{ai_response}'")
        
        # Save AI response to database
        ai_message = Message(
            user_id=user.id,
            sender_type='ai',
            text=ai_response
        )
        db.session.add(ai_message)
        db.session.commit()
        logging.info(f"💾 AI response saved to database")

        # Send SMS reply
        logging.info(f"📤 Attempting to send SMS reply to {sender_phone}")
        sms_sent = sms_service.send_sms(sender_phone, ai_response)
        
        if sms_sent:
            logging.info(f"✅ Successfully processed and replied to {sender_phone}")
        else:
            logging.error(f"❌ Failed to send SMS reply to {sender_phone}")

    except Exception as e:
        logging.error(f"💥 Error processing SMS from {sender_phone}: {e}")
        db.session.rollback()
        
        # Send a simple error message to user
        try:
            sms_service.send_sms(sender_phone, "Sorry, I'm having technical difficulties. Please try again.")
        except:
            pass

    # Always return 200 OK to Africa's Talking
    return Response("OK", status=200)

@sms_bp.route('/send_sms', methods=['POST'])
def manual_send_sms():
    """Manual SMS sending endpoint for testing."""
    data = request.get_json()
    
    if not data or 'phone' not in data or 'message' not in data:
        return jsonify({"error": "Phone and message required"}), 400
    
    phone = data['phone']
    message = data['message']
    
    if sms_service.send_sms(phone, message):
        return jsonify({"status": "sent", "phone": phone, "message": message})
    else:
        return jsonify({"error": "Failed to send SMS"}), 500

@sms_bp.route('/test_sms', methods=['POST', 'GET'])
def test_sms():
    """Test SMS sending functionality."""
    if request.method == 'GET':
        return '''
        <form method="POST">
            <input type="text" name="phone" placeholder="+254XXXXXXXXX" required><br>
            <textarea name="message" placeholder="Test message" required></textarea><br>
            <button type="submit">Send Test SMS</button>
        </form>
        '''
    
    phone = request.form.get('phone')
    message = request.form.get('message')
    
    if not phone or not message:
        return "Phone and message required", 400
    
    success = sms_service.send_sms(phone, message)
    
    if success:
        return f"✅ SMS sent successfully to {phone}"
    else:
        return f"❌ Failed to send SMS to {phone}", 500 