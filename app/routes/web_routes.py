from flask import Blueprint, request, jsonify, render_template_string, session
import logging
from datetime import datetime
from app.services.ai_service import ai_service
from app.templates.chat_template import CHAT_TEMPLATE
from app.models.models import db, Message

web_bp = Blueprint('web', __name__)

# Store web chat sessions (in production, use Redis or database)
web_chat_sessions = {}

@web_bp.route('/')
def index():
    """Root route - redirect to chat."""
    return '<h1>SuperiaTech Learning Platform</h1><p><a href="/chat">Go to Chat Interface</a></p><p><a href="/health">Health Check</a></p>'

@web_bp.route('/chat')
def chat_interface():
    """Serve the chat interface."""
    try:
        return render_template_string(CHAT_TEMPLATE)
    except Exception as e:
        logging.error(f"Error rendering chat template: {e}")
        return f"Error loading chat interface: {str(e)}", 500

@web_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    session_id = data.get('session_id', 'default')
    if not message:
        return jsonify({'error': 'Message required'}), 400
    try:
        # Save user message
        user_message = Message(
            user_id=None,  # Not linked to a user for web chat
            sender_type='user',
            text=message
        )
        db.session.add(user_message)
        db.session.commit()
        # Get conversation history (last 20 messages)
        conversation_history = Message.query.order_by(Message.timestamp.asc()).limit(20).all()
        history_text = '\n'.join([m.text for m in conversation_history])
        # Generate AI response
        ai_response = ai_service.generate_response(message, history_text)
        # Save AI response
        ai_message = Message(
            user_id=None,
            sender_type='ai',
            text=ai_response
        )
        db.session.add(ai_message)
        db.session.commit()
        return jsonify({'response': ai_response})
    except Exception as e:
        logging.error(f"Error in /chat: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@web_bp.route('/api/chat', methods=['POST'])
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
        ai_response = ai_service.generate_response(message_text, conversation_history)
        
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

@web_bp.route('/api/chat_history/<session_id>')
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

@web_bp.route('/api/cleanup_sessions', methods=['POST'])
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

@web_bp.route('/chat_history', methods=['GET'])
def chat_history():
    session_id = request.args.get('session_id') or request.cookies.get('session_id') or request.headers.get('X-Session-Id')
    if not session_id:
        session_id = 'default'  # fallback for demo
    # For demo, just return the last 50 messages (in real app, filter by session_id or user)
    messages = Message.query.order_by(Message.timestamp.asc()).limit(50).all()
    messages_json = [
        {
            'text': m.text,
            'sender_type': m.sender_type,
            'timestamp': m.timestamp.isoformat() if m.timestamp else datetime.utcnow().isoformat()
        } for m in messages
    ]
    return jsonify({'messages': messages_json}) 