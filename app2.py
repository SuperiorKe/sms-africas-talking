# app.py - Fixed Two-Way SMS Implementation with Web Chat
from flask import Flask, request, Response, current_app, render_template_string, jsonify
import africastalking
import os
from dotenv import load_dotenv
import logging
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import uuid

# Store web chat sessions (in production, use Redis or database)
web_chat_sessions = {}

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)

# Load configurations
app.config['AT_USERNAME'] = os.getenv("AT_USERNAME")
app.config['AT_API_KEY'] = os.getenv("AT_API_KEY")
app.config['GEMINI_API_KEY'] = os.getenv("GEMINI_API_KEY")

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sms_learning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    messages = db.relationship('Message', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.phone_number}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.id} by {self.sender_type}>'

# Global service instances
sms_service_global = None
gemini_model_global = None

def initialize_external_services(current_flask_app):
    """Initialize Africa's Talking and Gemini services."""
    global sms_service_global, gemini_model_global

    # Initialize Africa's Talking
    at_user = current_flask_app.config.get('AT_USERNAME')
    at_key = current_flask_app.config.get('AT_API_KEY')
    
    if not at_user or not at_key:
        logging.error("Africa's Talking credentials not configured.")
        return False
    
    try:
        africastalking.initialize(at_user, at_key)
        sms_service_global = africastalking.SMS
        logging.info("Africa's Talking SDK Initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Africa's Talking SDK: {e}")
        return False

    # Initialize Gemini
    gem_key = current_flask_app.config.get('GEMINI_API_KEY')
    if not gem_key:
        logging.error("GEMINI_API_KEY not configured.")
        return False
    
    try:
        genai.configure(api_key=gem_key)
        gemini_model_global = genai.GenerativeModel('gemini-2.0-flash')
        logging.info("Gemini Model Initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Gemini Model: {e}")
        gemini_model_global = None
        return False
    
    return True

# Key improvements to ensure SMS responses work properly

# 1. Enhanced SMS sending function with better error handling
def send_sms_reply(phone_number, message):
    """Send SMS reply using Africa's Talking API with proper two-way configuration."""
    if not sms_service_global:
        logging.error("SMS service not initialized")
        return False
    
    # Ensure phone number is properly formatted
    if not phone_number.startswith('+'):
        if phone_number.startswith('254'):
            phone_number = '+' + phone_number
        elif phone_number.startswith('0'):
            phone_number = '+254' + phone_number[1:]
        else:
            phone_number = '+254' + phone_number
    
    try:
        # For two-way SMS, don't specify sender_id - let AT use the shortcode
        response = sms_service_global.send(
            message=message,
            recipients=[phone_number]
            # sender_id=None is default - AT will use your registered shortcode
        )
        
        logging.info(f"SMS API Response: {response}")
        
        # Check if message was sent successfully
        if response and 'SMSMessageData' in response:
            recipients = response['SMSMessageData'].get('Recipients', [])
            for recipient in recipients:
                if recipient.get('status') == 'Success':
                    logging.info(f"✅ SMS sent successfully to {recipient.get('number')}")
                    return True
                else:
                    logging.error(f"❌ SMS failed to {recipient.get('number')}: {recipient.get('status')}")
                    return False
        else:
            logging.error(f"Invalid AT response structure: {response}")
            return False
        
    except Exception as e:
        logging.error(f"Exception sending SMS to {phone_number}: {e}")
        return False
    
    return False

# 2. Enhanced SMS callback with better error handling and logging
@app.route('/sms_callback', methods=['POST'])
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
            text=message_text
        )
        db.session.add(user_message)
        db.session.commit()
        logging.info(f"💾 User message saved to database")

        # Get conversation history
        conversation_history = get_conversation_history(user.id)
        logging.info(f"📚 Retrieved conversation history: {len(conversation_history.split('\\n'))} messages")
        
        # Generate AI response
        logging.info(f"🤖 Generating AI response...")
        ai_response = generate_ai_response(message_text, conversation_history)
        logging.info(f"🤖 AI Response generated: '{ai_response}'")
        
        # Save AI response to database FIRST
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
        sms_sent = send_sms_reply(sender_phone, ai_response)
        
        if sms_sent:
            logging.info(f"✅ Successfully processed and replied to {sender_phone}")
        else:
            logging.error(f"❌ Failed to send SMS reply to {sender_phone}")
            # You might want to set a flag in the database to retry later

    except Exception as e:
        logging.error(f"💥 Error processing SMS from {sender_phone}: {e}")
        db.session.rollback()
        
        # Send a simple error message to user
        try:
            send_sms_reply(sender_phone, "Sorry, I'm having technical difficulties. Please try again.")
        except:
            pass

    # Always return 200 OK to Africa's Talking
    return Response("OK", status=200)

# 3. Enhanced AI response generation with better error handling
def generate_ai_response(message_text, conversation_history):
    """Generate AI response using Gemini with better error handling."""
    if not gemini_model_global:
        logging.error("Gemini model not initialized")
        return "Sorry, I'm currently unavailable. Please try again later."
    
    try:
        # Improved prompt for Kenyan artisans
        prompt = f"""You are an AI SMS Learning Tutor for skilled artisans and workers in Nairobi, Kenya.

Your role:
- Help with work-related questions, business advice, and skill development
- Provide practical solutions for craftspeople, technicians, and small business owners
- Keep responses SHORT (under 160 characters for SMS)
- Be encouraging, supportive, and culturally aware
- Focus on actionable advice that works in Nairobi context
- Use simple, clear language

Conversation history:
{conversation_history}

Current message: {message_text}

Provide a helpful, concise SMS response (max 160 characters):"""

        logging.info(f"🤖 Sending prompt to Gemini...")
        
        response = gemini_model_global.generate_content(prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            ai_text = response.candidates[0].content.parts[0].text.strip()
            
            # Ensure response is SMS-friendly
            if len(ai_text) > 160:
                ai_text = ai_text[:157] + "..."
            
            logging.info(f"🤖 Generated response ({len(ai_text)} chars): {ai_text}")
            return ai_text
        else:
            logging.warning("Empty Gemini response")
            return "I'm having trouble understanding. Could you rephrase?"
            
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        return "Technical error. Please try again."

# 4. Add a test endpoint to manually send SMS
@app.route('/test_sms', methods=['POST', 'GET'])
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
    
    success = send_sms_reply(phone, message)
    
    if success:
        return f"✅ SMS sent successfully to {phone}"
    else:
        return f"❌ Failed to send SMS to {phone}", 500



# Initialize database and services
db.init_app(app)

# HTML template for the chat interface
CHAT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SuperiaTech Learning Chat</title>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        /* General Reset and Body Styling */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Google Sans', 'Roboto', Arial, sans-serif;
            background-color: #f0f3f6; /* Light grey background inspired by Gemini */
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #202124; /* Darker text for readability */
        }

        /* Chat Container */
        .chat-container {
            width: 100%;
            max-width: 900px; /* Slightly wider */
            height: 90vh;
            background: #ffffff;
            border-radius: 24px; /* More rounded corners */
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1); /* Softer shadow */
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: all 0.3s ease-in-out;
        }

        /* Chat Header */
        .chat-header {
            background-color: #ffffff; /* White background */
            color: #202124; /* Dark text */
            padding: 20px 30px;
            border-bottom: 1px solid #e0e0e0; /* Subtle border */
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
        }

        .chat-header h1 {
            font-size: 1.6rem; /* Slightly larger title */
            font-weight: 500; /* Medium weight */
            color: #1a73e8; /* Google Blue for emphasis */
        }

        .chat-header p {
            font-size: 0.95rem;
            color: #5f6368; /* Google grey for subtitle */
        }

        /* Messages Container */
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px 30px;
            background: #f8f9fa; /* Lighter background for messages area */
            scroll-behavior: smooth;
        }

        /* Message Styling */
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }

        .message.user {
            justify-content: flex-end;
        }

        .message.ai {
            justify-content: flex-start;
        }

        .message-bubble {
            max-width: 75%; /* Slightly wider bubbles */
            padding: 14px 20px;
            border-radius: 20px; /* More rounded */
            position: relative;
            word-wrap: break-word;
            font-size: 1rem;
            line-height: 1.5;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08); /* Subtle shadow for bubbles */
        }

        .message.user .message-bubble {
            background-color: #1a73e8; /* Google Blue for user messages */
            color: white;
            border-bottom-right-radius: 4px; /* Pointy corner for user */
        }

        .message.ai .message-bubble {
            background-color: #e8f0fe; /* Light blue for AI messages */
            color: #202124;
            border-bottom-left-radius: 4px; /* Pointy corner for AI */
        }

        .message-time {
            font-size: 0.75rem;
            opacity: 0.7;
            margin-top: 8px;
            display: block;
            text-align: right;
            color: inherit; /* Inherit color from bubble */
        }
        
        .message.ai .message-time {
            text-align: left;
        }

        /* Typing Indicator */
        .typing-indicator {
            display: none;
            padding: 10px 30px;
            font-style: italic;
            color: #5f6368;
            font-size: 0.9rem;
        }

        /* Input Container */
        .input-container {
            padding: 15px 30px;
            background: #ffffff;
            border-top: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .message-input {
            flex: 1;
            padding: 12px 20px;
            border: 1px solid #dadce0; /* Lighter border */
            border-radius: 24px; /* Fully rounded */
            outline: none;
            font-size: 1rem;
            transition: border-color 0.3s, box-shadow 0.3s;
            background-color: #f1f3f4; /* Light grey background for input */
        }

        .message-input:focus {
            border-color: #1a73e8; /* Blue border on focus */
            box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2); /* Subtle blue glow */
            background-color: #ffffff; /* White background on focus */
        }

        .send-button {
            width: 48px;
            height: 48px;
            border: none;
            border-radius: 50%;
            background-color: #1a73e8; /* Google Blue */
            color: white;
            font-size: 1.5rem; /* Larger icon */
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: background-color 0.3s, transform 0.2s;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* Subtle shadow */
        }

        .send-button:hover:not(:disabled) {
            background-color: #174ea6; /* Darker blue on hover */
            transform: scale(1.05);
        }

        .send-button:disabled {
            background-color: #e0e0e0; /* Grey when disabled */
            color: #a0a0a0;
            cursor: not-allowed;
            box-shadow: none;
        }

        /* Responsive Adjustments */
        @media (max-width: 768px) {
            .chat-container {
                height: 100vh;
                border-radius: 0;
                box-shadow: none;
            }

            .chat-header {
                padding: 15px 20px;
            }

            .messages-container {
                padding: 15px 20px;
            }

            .message-bubble {
                max-width: 85%;
            }

            .input-container {
                padding: 10px 20px;
            }
            
            .message-input {
                padding: 10px 15px;
            }

            .send-button {
                width: 44px;
                height: 44px;
                font-size: 1.3rem;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>SuperiaTech Learning Assistant</h1>
            <p>Your AI tutor for skill development and business growth</p>
        </div>
        
        <div class="messages-container" id="messagesContainer">
            <div class="message ai">
                <div class="message-bubble">
                    Hello! I'm your SuperiaTech Learning Assistant. I'm here to help you with work-related questions, skill development, and business advice. How can I assist you today?
                    <div class="message-time">Just now</div>
                </div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            Assistant is typing<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
        </div>
        
        <div class="input-container">
            <input type="text" 
                   class="message-input" 
                   id="messageInput" 
                   placeholder="Type your message here..." 
                   maxlength="500">
            <button class="send-button" id="sendButton">
                <i class="material-icons">send</i>
            </button>
        </div>
    </div>

    <script>
        class ChatInterface {
            constructor() {
                this.messagesContainer = document.getElementById('messagesContainer');
                this.messageInput = document.getElementById('messageInput');
                this.sendButton = document.getElementById('sendButton');
                this.typingIndicator = document.getElementById('typingIndicator');
                this.sessionId = this.generateSessionId();
                
                this.init();
            }

            generateSessionId() {
                return 'web_' + Math.random().toString(36).substr(2, 9);
            }

            init() {
                this.sendButton.addEventListener('click', () => this.sendMessage());
                this.messageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.sendMessage();
                    }
                });
                this.messageInput.focus();
                this.messageInput.addEventListener('input', () => this.toggleSendButton());
                this.toggleSendButton(); // Initial check
            }

            toggleSendButton() {
                this.sendButton.disabled = this.messageInput.value.trim().length === 0;
            }

            async sendMessage() {
                const message = this.messageInput.value.trim();
                if (!message) return;

                this.setLoading(true);
                this.addMessage(message, 'user');
                this.messageInput.value = '';
                this.toggleSendButton(); // Disable after sending
                this.showTyping();

                try {
                    // This fetch call is a placeholder. 
                    // In a real application, you'd replace '/api/chat' with your actual backend endpoint
                    // and handle potential CORS issues or API key requirements.
                    const response = await fetch('/api/chat', { 
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            session_id: this.sessionId
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    
                    this.hideTyping();
                    
                    if (data.success) {
                        this.addMessage(data.response, 'ai');
                    } else {
                        // Display a more user-friendly error message if the API indicates failure
                        this.addMessage(data.error || 'Sorry, I encountered an error. Please try again.', 'ai');
                    }
                    
                } catch (error) {
                    console.error('Error:', error);
                    this.hideTyping();
                    this.addMessage('Connection error. Please check your internet and try again.', 'ai');
                } finally {
                    this.setLoading(false);
                    this.toggleSendButton(); // Re-enable if input has text after response
                }
            }

            addMessage(text, sender) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                
                const now = new Date();
                const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                
                messageDiv.innerHTML = `
                    <div class="message-bubble">
                        ${this.escapeHtml(text)}
                        <div class="message-time">${timeString}</div>
                    </div>
                `;

                this.messagesContainer.appendChild(messageDiv);
                this.scrollToBottom();
            }

            escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }

            showTyping() {
                this.typingIndicator.style.display = 'block';
                this.scrollToBottom();
            }

            hideTyping() {
                this.typingIndicator.style.display = 'none';
            }

            setLoading(loading) {
                this.sendButton.disabled = loading;
                this.messageInput.disabled = loading;
                
                if (loading) {
                    // Using Material Icon for sending state
                    this.sendButton.innerHTML = '<i class="material-icons">hourglass_empty</i>'; 
                } else {
                    this.sendButton.innerHTML = '<i class="material-icons">send</i>';
                    this.messageInput.focus();
                }
            }

            scrollToBottom() {
                setTimeout(() => {
                    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
                }, 100);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            new ChatInterface();
        });
    </script>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    """Root route - redirect to chat."""
    return '<h1>SuperiaTech Learning Platform</h1><p><a href="/chat">Go to Chat Interface</a></p><p><a href="/health">Health Check</a></p>'

@app.route('/chat')
def chat_interface():
    """Serve the chat interface."""
    try:
        return render_template_string(CHAT_TEMPLATE)
    except Exception as e:
        logging.error(f"Error rendering chat template: {e}")
        return f"Error loading chat interface: {str(e)}", 500

@app.route('/sms_callback', methods=['POST'])
def sms_callback():
    """Handle incoming SMS messages from Africa's Talking webhook."""
    
    # Validate request
    if not request.form:
        logging.error("Empty form data received")
        return Response("Bad Request", status=400)

    # Extract SMS data
    sender_phone = request.form.get('from')
    message_text = request.form.get('text', '').strip()
    link_id = request.form.get('linkId')  # Useful for tracking
    
    logging.info(f"SMS received - From: {sender_phone}, Message: '{message_text}', LinkID: {link_id}")

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
            logging.info(f"New user created: {sender_phone}")

        # Save incoming message
        user_message = Message(
            user_id=user.id, 
            sender_type='user', 
            text=message_text
        )
        db.session.add(user_message)
        db.session.commit()

        # Get conversation history
        conversation_history = get_conversation_history(user.id)
        
        # Generate AI response
        ai_response = generate_ai_response(message_text, conversation_history)
        
        # Save AI response to database
        ai_message = Message(
            user_id=user.id,
            sender_type='ai',
            text=ai_response
        )
        db.session.add(ai_message)
        db.session.commit()

        # Send SMS reply
        if send_sms_reply(sender_phone, ai_response):
            logging.info(f"Successfully processed and replied to {sender_phone}")
        else:
            logging.error(f"Failed to send reply to {sender_phone}")

    except Exception as e:
        logging.error(f"Error processing SMS from {sender_phone}: {e}")
        db.session.rollback()

    return Response("OK", status=200)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle web chat messages."""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data or 'session_id' not in data:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
        message_text = data['message'].strip()
        session_id = data['session_id']
        
        if not message_text:
            return jsonify({'success': False, 'error': 'Empty message'}), 400
        
        logging.info(f"Web chat message - Session: {session_id}, Message: '{message_text}'")
        
        # Get or create web session
        if session_id not in web_chat_sessions:
            web_chat_sessions[session_id] = {
                'messages': [],
                'created_at': datetime.utcnow()
            }
        
        session = web_chat_sessions[session_id]
        
        # Add user message to session
        session['messages'].append({
            'sender': 'user',
            'text': message_text,
            'timestamp': datetime.utcnow()
        })
        
        # Keep only last 10 messages for context
        if len(session['messages']) > 10:
            session['messages'] = session['messages'][-10:]
        
        # Generate conversation history
        history_parts = []
        for msg in session['messages'][-6:]:  # Last 6 messages for context
            role = "User" if msg['sender'] == 'user' else "Assistant"
            history_parts.append(f"{role}: {msg['text']}")
        
        conversation_history = "\n".join(history_parts)
        
        # Generate AI response
        ai_response = generate_ai_response_web(message_text, conversation_history)
        
        # Add AI response to session
        session['messages'].append({
            'sender': 'ai',
            'text': ai_response,
            'timestamp': datetime.utcnow()
        })
        
        logging.info(f"Web chat response - Session: {session_id}, Response: '{ai_response}'")
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'session_id': session_id
        })
        
    except Exception as e:
        logging.error(f"Error in web chat API: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# 5. Enhanced health check
@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint."""
    at_status = sms_service_global is not None
    gemini_status = gemini_model_global is not None
    
    # Test database connection
    try:
        db.session.execute('SELECT 1')
        db_status = True
    except:
        db_status = False
    
    # Test Africa's Talking credentials
    try:
        if sms_service_global:
            # This is a simple check - you might want to make an actual API call
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
            "at_username": app.config.get('AT_USERNAME', 'Not set'),
            "webhook_url": request.host_url + 'sms_callback'
        }
    })

# Optional: Manual SMS sending endpoint for testing
@app.route('/send_sms', methods=['POST'])
def manual_send_sms():
    """Manual SMS sending endpoint for testing."""
    data = request.get_json()
    
    if not data or 'phone' not in data or 'message' not in data:
        return {"error": "Phone and message required"}, 400
    
    phone = data['phone']
    message = data['message']
    
    if send_sms_reply(phone, message):
        return {"status": "sent", "phone": phone, "message": message}
    else:
        return {"error": "Failed to send SMS"}, 500

# Optional: Clean up old web sessions periodically
@app.route('/api/cleanup_sessions', methods=['POST'])
def cleanup_old_sessions():
    """Clean up old web chat sessions (call this periodically)."""
    try:
        current_time = datetime.utcnow()
        sessions_to_remove = []
        
        for session_id, session_data in web_chat_sessions.items():
            # Remove sessions older than 1 hour
            if (current_time - session_data['created_at']).seconds > 3600:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del web_chat_sessions[session_id]
        
        logging.info(f"Cleaned up {len(sessions_to_remove)} old web chat sessions")
        
        return jsonify({
            'success': True,
            'cleaned_sessions': len(sessions_to_remove),
            'active_sessions': len(web_chat_sessions)
        })
        
    except Exception as e:
        logging.error(f"Error cleaning up sessions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat_history/<session_id>')
def get_chat_history(session_id):
    """Get chat history for a session."""
    if session_id in web_chat_sessions:
        messages = web_chat_sessions[session_id]['messages']
        return jsonify({
            'success': True,
            'messages': [
                {
                    'sender': msg['sender'],
                    'text': msg['text'],
                    'timestamp': msg['timestamp'].isoformat()
                }
                for msg in messages
            ]
        })
    else:
        return jsonify({'success': False, 'error': 'Session not found'}), 404

# Initialize the app
with app.app_context():
    db.create_all()
    logging.info("Database tables created/verified.")
    
    if initialize_external_services(app):
        logging.info("All services initialized successfully.")
    else:
        logging.error("Failed to initialize some services.")

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')