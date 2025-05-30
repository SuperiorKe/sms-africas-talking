# SuperiaTech Learning Platform

A Flask-based SMS and web chat platform that uses Africa's Talking for SMS messaging and Google's Gemini AI for intelligent responses.

## Features

- SMS-based chat interface using Africa's Talking
- Web-based chat interface
- AI-powered responses using Google's Gemini
- User session management
- Health monitoring endpoints
- Database storage for messages and users

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```
FLASK_APP=run.py
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///sms_learning.db

# Africa's Talking credentials
AT_USERNAME=your-at-username
AT_API_KEY=your-at-api-key

# Google Gemini credentials
GEMINI_API_KEY=your-gemini-api-key
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Start the Flask development server:
```bash
python run.py
```

2. For production deployment:
```bash
gunicorn run:app
```

## API Endpoints

### SMS Endpoints
- `POST /sms_callback`: Africa's Talking webhook for incoming SMS
- `POST /send_sms`: Manual SMS sending endpoint
- `GET/POST /test_sms`: Test SMS functionality

### Web Chat Endpoints
- `GET /`: Home page
- `GET /chat`: Web chat interface
- `POST /api/chat`: Web chat message endpoint
- `GET /api/chat_history/<session_id>`: Get chat history
- `POST /api/cleanup_sessions`: Clean up old sessions

### Health Check
- `GET /health`: System health status

## Development

The application is structured as follows:
```
app/
├── config/         # Configuration settings
├── models/         # Database models
├── routes/         # Route handlers
├── services/       # External service integrations
├── static/         # Static files
└── templates/      # HTML templates
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 