# send_sms.py (cleaned up version)
import africastalking
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("AT_USERNAME")
api_key = os.getenv("AT_API_KEY")
your_test_phone = os.getenv("YOUR_TEST_PHONE_NUMBER")

if not username or not api_key or not your_test_phone:
    print("Please set AT_USERNAME, AT_API_KEY, and YOUR_TEST_PHONE_NUMBER in your .env file")
    exit()

africastalking.initialize(username, api_key)
sms = africastalking.SMS

recipients = [your_test_phone]
message = "Hello from my Africa's Talking Python app! Phase 1 test."

try:
    response = sms.send(message, recipients)
    print("SMS Sent Successfully!")
    print(f"Cost: {response['SMSMessageData']['Message']}")
    print(f"Status: {response['SMSMessageData']['Recipients'][0]['status']}")
except Exception as e:
    print(f"Houston, we have a problem: {e}")