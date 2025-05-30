import google.generativeai as genai
import logging
from flask import current_app

class AIService:
    def __init__(self):
        self.model = None
        self.initialized = False

    def initialize(self):
        """Initialize Gemini AI service."""
        try:
            genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.initialized = True
            logging.info("Gemini Model Initialized successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize Gemini Model: {e}")
            return False

    def generate_response(self, message_text, conversation_history):
        """Generate AI response using Gemini."""
        if not self.initialized:
            logging.error("AI model not initialized")
            return "Sorry, I'm currently unavailable. Please try again later."

        try:
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
            
            response = self.model.generate_content(prompt)
            
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

# Create a singleton instance
ai_service = AIService() 