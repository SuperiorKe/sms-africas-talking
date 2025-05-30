from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    messages = db.relationship('Message', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.phone_number}>'

    def update_last_active(self):
        self.last_active = datetime.utcnow()
        db.session.commit()

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    sender_type = db.Column(db.String(10), nullable=False)  # 'user' or 'ai'
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(10), default='sent')  # e.g., 'sent', 'failed', 'received', 'read'
    link_id = db.Column(db.String(50), nullable=True)  # For Africa's Talking SMS correlation

    def __repr__(self):
        return f'<Message from {self.sender_type} at {self.timestamp}>'

    @classmethod
    def get_conversation_history(cls, user_id, limit=10):
        """Retrieve conversation history for a user."""
        messages = cls.query.filter_by(user_id=user_id).order_by(cls.timestamp.asc()).limit(limit).all()
        history = ""
        for msg in messages:
            role = "User" if msg.sender_type == 'user' else "Assistant"
            history += f"{role}: {msg.text}\n"
        return history.strip() 