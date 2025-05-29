# app.py
from flask import Flask, request, Response, current_app # Import current_app
import africastalking
import os
from dotenv import load_dotenv
import logging
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --- Load environment variables VERY FIRST ---
load_dotenv()

# --- Configure basic logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Initialize Flask app ---
app = Flask(__name__)

# --- Load configurations into app.config ---
app.config['AT_USERNAME'] = os.getenv("AT_USERNAME")
app.config['AT_API_KEY'] = os.getenv("AT_API_KEY")
app.config['GEMINI_API_KEY'] = os.getenv("GEMINI_API_KEY") # Store Gemini key here

# --- Database Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sms_learning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy() # Initialize SQLAlchemy without the app first

# --- Define Database Models (User, Message) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    messages = db.relationship('Message', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.phone_number}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender_type = db.Column(db.String(10), nullable=False) # 'user' or 'ai'
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.id} by {self.sender_type}>'

# --- Global service instances (to be initialized with the app) ---
sms_service_global = None
gemini_model_global = None

def initialize_external_services(current_flask_app):
    """Initializes Africa's Talking and Gemini services."""
    global sms_service_global, gemini_model_global

    # Initialize Africa's Talking
    at_user = current_flask_app.config.get('AT_USERNAME')
    at_key = current_flask_app.config.get('AT_API_KEY')
    if not at_user or not at_key:
        logging.error("Africa's Talking credentials not fully configured.")
    else:
        try:
            africastalking.initialize(at_user, at_key)
            sms_service_global = africastalking.SMS
            logging.info("Africa's Talking SDK Initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize Africa's Talking SDK: {e}")


    # Initialize Gemini
    gem_key = current_flask_app.config.get('GEMINI_API_KEY')
    if not gem_key:
        logging.error("GEMINI_API_KEY not configured.")
    else:
        try:
            genai.configure(api_key=gem_key)
            gemini_model_global = genai.GenerativeModel('gemini-2.0-flash')
            logging.info("Gemini Model Initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize Gemini Model: {e}")
            gemini_model_global = None # Ensure it's None if init fails

# Initialize SQLAlchemy with the app
db.init_app(app)

# Create database tables and initialize services within app context
with app.app_context():
    db.create_all()
    logging.info("Database tables checked/created.")
    initialize_external_services(app) # Initialize AT and Gemini


@app.route('/sms_callback', methods=['POST'])
def sms_callback():
    if not request.form:
        logging.error("Received empty form data.")
        return "Error: No form data received", 400

    sender_phone = request.form.get('from')
    message_text = request.form.get('text')
    # ... (other AT fields)

    logging.info(f"Received SMS from: {sender_phone}, Message: {message_text}")

    # --- Database Interaction ---
    user = User.query.filter_by(phone_number=sender_phone).first()
    if not user:
        user = User(phone_number=sender_phone)
        db.session.add(user)
        db.session.commit()
        logging.info(f"New user created: {sender_phone}")

    user_message_db = Message(user_id=user.id, sender_type='user', text=message_text)
    db.session.add(user_message_db)
    db.session.commit()
    logging.info(f"Saved user message for {sender_phone}")

    conversation_history_str = ""
    recent_messages = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).limit(6).all()
    recent_messages.reverse()
    history_for_prompt = []
    for msg in recent_messages: # Include current message by querying before AI response
        if msg.sender_type == 'user':
            history_for_prompt.append(f"User: {msg.text}")
        else:
            history_for_prompt.append(f"Tutor: {msg.text}")
    conversation_history_str = "\n".join(history_for_prompt)
    logging.info(f"Conversation history for prompt:\n{conversation_history_str}")


    # --- Call Gemini API ---
    reply_message_text = "Sorry, I couldn't process your request at the moment."
    
    # Access Gemini API key from app.config and check if model is initialized
    current_gemini_api_key = current_app.config.get('GEMINI_API_KEY')

    if message_text and current_gemini_api_key and gemini_model_global:
        try:
            prompt = f"""You are an AI SMS Learning Tutor.
Keep your responses very short and concise, suitable for SMS (max 1-2 sentences, ideally under 160 characters).
Here is the recent conversation history (most recent message is the user's current input):
{conversation_history_str}

Based on this history, and especially the last user message, provide a helpful educational response or answer.
"""
            logging.info(f"Sending prompt to Gemini:\n{prompt}")
            gemini_response = gemini_model_global.generate_content(prompt)

            if gemini_response.candidates and gemini_response.candidates[0].content.parts:
                ai_generated_text = gemini_response.candidates[0].content.parts[0].text
                reply_message_text = ai_generated_text.strip()
                logging.info(f"Gemini Response: {reply_message_text}")

                ai_message_db = Message(user_id=user.id, sender_type='ai', text=reply_message_text)
                db.session.add(ai_message_db)
                db.session.commit()
                logging.info(f"Saved AI response for {sender_phone}")
            else:
                logging.warning("Gemini response was empty or not in expected format.")
                if gemini_response.prompt_feedback:
                    logging.warning(f"Gemini Prompt Feedback: {gemini_response.prompt_feedback}")
                    # More specific handling for blocked content
                    for rating in gemini_response.prompt_feedback.safety_ratings:
                        if rating.probability.name not in ['NEGLIGIBLE', 'LOW']: # If probability is MEDIUM, HIGH, or unspecified but not safe
                            reply_message_text = "I cannot respond to that type of request due to safety guidelines."
                            break 

        except Exception as e:
            logging.error(f"Error calling Gemini API: {e}")
    else:
        if not current_gemini_api_key or not gemini_model_global:
            logging.warning("Gemini API/Model not configured. Sending static reply.")
            reply_message_text = f"Hi {sender_phone}! We received your message: '{message_text}'. (AI is currently offline)."

    # --- Send reply via Africa's Talking ---
    if sender_phone and sms_service_global:
        try:
            recipients = [sender_phone]
            at_response = sms_service_global.send(reply_message_text, recipients)
            logging.info(f"Reply sent to {sender_phone} via AT: {at_response}")
        except Exception as e:
            logging.error(f"Error sending AT reply to {sender_phone}: {e}")
    else:
        logging.warning("Could not send reply: Sender phone or AT service unavailable.")

    return Response("OK", status=200, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, port=5000)