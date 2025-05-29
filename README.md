# SMS API Integration with Africa's Talking

This project demonstrates how to integrate with Africa's Talking SMS API using Python and Flask. It provides functionality to send SMS messages and receive incoming messages through a webhook.

## Features

- Send SMS messages using Africa's Talking API
- Receive incoming SMS messages via webhook
- Environment variable configuration for secure credential management
- Ngrok integration for local development and testing

## Prerequisites

- Python 3.x
- Africa's Talking account (sandbox or production)
- Ngrok account (for local development)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your Africa's Talking credentials:
```
AT_USERNAME=your_username
AT_API_KEY=your_api_key
```

## Configuration

### Africa's Talking Setup
1. Sign up for an Africa's Talking account at https://africastalking.com/
2. Get your API credentials from the dashboard
3. For testing, use the sandbox environment:
   - Username: `sandbox`
   - API Key: Get from your sandbox dashboard

### Ngrok Setup (for local development)
1. Sign up for a free ngrok account at https://ngrok.com/
2. Download and install ngrok
3. Configure your authtoken:
```bash
ngrok config add-authtoken your_ngrok_token
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. The application will:
   - Initialize the Africa's Talking SDK
   - Start a local server on port 5000
   - Create an ngrok tunnel for webhook access
   - Print the public URL for webhook configuration

3. Configure your Africa's Talking webhook:
   - Log in to your Africa's Talking dashboard
   - Set the callback URL to your ngrok URL + `/incoming-messages`
   - Example: `https://your-ngrok-url.ngrok.io/incoming-messages`

## Project Structure

- `app.py`: Main Flask application with webhook endpoints
- `send_sms.py`: SMS sending functionality using Africa's Talking SDK
- `.env`: Environment variables for credentials
- `requirements.txt`: Project dependencies

## API Endpoints

- `POST /incoming-messages`: Webhook endpoint for receiving SMS messages
  - Receives JSON data from Africa's Talking
  - Prints incoming message details to console

## Error Handling

The application includes comprehensive error handling for:
- Missing credentials
- SDK initialization failures
- SMS sending failures
- Webhook processing errors

## Security Notes

- Never commit your `.env` file or API credentials
- Use environment variables for sensitive data
- Keep your ngrok authtoken secure
- Use HTTPS in production

## Troubleshooting

1. If you get permission errors with ngrok:
   - Run PowerShell as Administrator
   - Check ngrok.exe permissions
   - Verify your authtoken is correct

2. If SMS sending fails:
   - Verify your Africa's Talking credentials
   - Check your account balance
   - Ensure your sender ID is approved (if using one)

## License

[Your chosen license]

## Contributing

[Your contribution guidelines] 