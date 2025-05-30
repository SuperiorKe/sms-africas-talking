# SMS AI Learning Platform

## Project Description

This project is a Flask-based application that integrates with Africa's Talking SMS API and Google's Gemini AI to create both an SMS-based and a web-based chat interface. It allows users to interact with an AI assistant via SMS and through a modern web chat interface, storing conversations in a database.

## Features

*   **SMS Integration**: Send and receive messages via Africa's Talking SMS API.
*   **Web Chat Interface**: A modern, mobile-responsive web interface for chatting with the AI.
*   **AI Powered Responses**: Utilizes Google's Gemini AI for generating chat responses.
*   **Conversation History**: Stores conversation history in an SQLite database.
*   **User and Message Management**: Database models for managing users (based on phone numbers) and messages.
*   **Modular Structure**: Application is organized into blueprints, services, and models for better maintainability.
*   **Database Migrations**: Uses Flask-Migrate for managing database schema changes.
*   **Health Check**: An endpoint (`/health`) to check the application's status.

## Project Structure

```
SMS AI Learning/
├── app/
│   ├── __init__.py         # Application factory and configuration
│   │   ├── __init__.py
│   │   └── config.py     # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py     # Database models (User, Message)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health_routes.py  # Health check blueprint
│   │   ├── sms_routes.py     # SMS callback and sending blueprint
│   │   └── web_routes.py     # Web chat interface and API blueprint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py     # Google Gemini AI integration
│   │   └── sms_service.py    # Africa's Talking SMS integration
│   └── templates/
│       └── chat_template.py  # HTML template for the web chat interface
├── migrations/             # Flask-Migrate directory
│   ├── versions/           # Migration scripts
│   ├── env.py
│   └── script.py.mako
├── .env.example            # Example environment file
├── .gitignore              # Specifies intentionally untracked files
├── README.md               # Project documentation (this file)
├── requirements.txt        # Python dependencies
└── run.py                  # Entry point to run the Flask application
```

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/SuperiorKe/sms-africas-talking
    cd SMS\ AI\ Learning
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Create a `.env` file:**

    Copy the `.env.example` file and rename it to `.env`. Update the placeholder values with your actual credentials and settings.

    ```dotenv
    FLASK_APP=run.py
    FLASK_DEBUG=True
    SECRET_KEY=your_secret_key_for_flask_sessions
    DATABASE_URL=sqlite:///sms_learning.db
    AT_USERNAME=your_africastalking_username
    AT_API_KEY=your_africastalking_api_key
    GEMINI_API_KEY=your_google_gemini_api_key
    ```
    *Replace `your_secret_key_for_flask_sessions`, `your_africastalking_username`, `your_africastalking_api_key`, and `your_google_gemini_api_key` with your actual values.*

6.  **Initialize and apply database migrations:**

    ```bash
    flask --app run.py db init
    flask --app run.py db migrate -m "initial migration"
    flask --app run.py db upgrade
    ```

## Running the Application

1.  **Ensure your virtual environment is activated.**
2.  **Ensure your `.env` file is correctly configured.**
3.  **Run the Flask application:**

    ```bash
    python run.py
    ```

    The application will be accessible at `http://127.0.0.1:5000` or `http://localhost:5000`.

## API Endpoints

*   `GET /`: Redirects to `/chat`.
*   `GET /chat`: Serves the web chat interface.
*   `POST /chat`: Accepts POST requests with a `message` and `session_id` (optional) to interact with the AI via the web interface.
*   `GET /chat_history`: Returns the chat history for the current session (limited for demo).
*   `POST /sms/sms_callback`: Africa's Talking webhook endpoint for incoming SMS messages.
*   `POST /sms/send_sms`: Manual endpoint to send an SMS (requires `phone` and `message` in JSON body).
*   `GET /sms/test_sms`, `POST /sms/test_sms`: Endpoint to manually test SMS sending via a simple web form.
*   `GET /health`: Health check endpoint.

## Development

*   To generate new migrations after changing `app/models/models.py`:
    ```bash
    flask --app run.py db migrate -m "a meaningful message about your changes"
    flask --app run.py db upgrade
    ```

## Contributing

Feel free to fork the repository, open issues, or submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.