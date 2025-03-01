import google.generativeai as genai
import logging
from werkzeug.exceptions import BadRequest, InternalServerError

logger = logging.getLogger(__name__)

class Chatbot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.setup_model()

    def setup_model(self):
        """Initialize the Gemini model with API key"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('models/gemini-2.0-flash')
            logger.info("Successfully initialized Gemini model with v1beta API")
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}")
            raise

    def generate_response(self, message):
        """Generate a response using the Gemini model"""
        try:
            logger.info("Sending request to Gemini API")
            structured_prompt = """You are an AI-powered medical assistant, designed to help users understand their symptoms and suggest possible medical conditions. Your responses should be concise, direct, and professional, without unnecessary elaboration. You do not provide official diagnoses or medical advice but instead guide users towards potential concerns and recommend a relevant medical specialist or general physician.

If the user describes symptoms, always ask them to rate the severity on a scale of 1-10.

Remember:
1. Always maintain a professional tone
2. Be concise and direct
3. Do not provide diagnoses
4. Guide users to appropriate medical professionals
5. Ask for symptom severity ratings
6. Remind users to seek emergency care (911) for severe symptoms

User's message: """ + message

            response = self.model.generate_content(structured_prompt)
            
            if not response.text:
                logger.error("Received empty response from Gemini")
                raise ValueError("Empty response from Gemini")
            
            logger.info("Successfully generated response from Gemini")
            return response.text

        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            raise InternalServerError(f"Error generating response from AI model: {str(e)}")

    def process_chat_request(self, data):
        """Process a chat request and return a response"""
        if not data.get('message'):
            logger.warning("No message provided in request")
            raise BadRequest("Message is required")

        message = data['message']
        logger.info(f"Processing message: {message[:50]}...")  # Log first 50 chars of message
        
        return self.generate_response(message)