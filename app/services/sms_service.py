import africastalking
import logging
from flask import current_app

class SMSService:
    def __init__(self):
        self.sms_service = None
        self.initialized = False

    def initialize(self):
        """Initialize Africa's Talking service."""
        try:
            africastalking.initialize(
                current_app.config['AT_USERNAME'],
                current_app.config['AT_API_KEY']
            )
            self.sms_service = africastalking.SMS
            self.initialized = True
            logging.info("Africa's Talking SDK Initialized successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize Africa's Talking SDK: {e}")
            return False

    def send_sms(self, phone_number, message):
        """Send SMS using Africa's Talking API."""
        if not self.initialized:
            logging.error("SMS service not initialized")
            return False

        # Format phone number
        if not phone_number.startswith('+'):
            if phone_number.startswith('254'):
                phone_number = '+' + phone_number
            elif phone_number.startswith('0'):
                phone_number = '+254' + phone_number[1:]
            else:
                phone_number = '+254' + phone_number

        try:
            response = self.sms_service.send(
                message=message,
                recipients=[phone_number]
            )

            logging.info(f"SMS API Response: {response}")

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

# Create a singleton instance
sms_service = SMSService() 