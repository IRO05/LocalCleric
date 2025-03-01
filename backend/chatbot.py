import google.generativeai as genai
import json
import logging
import requests
from werkzeug.exceptions import BadRequest, InternalServerError
#idk if this saved
logger = logging.getLogger(__name__)

PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

class Chatbot:
    def __init__(self, api_key, places_api_key):
        self.api_key = api_key
        self.places_api_key = places_api_key
        self.setup_model()

    def find_nearby_specialist(self, specialist_type, location=""):
        """Find nearby medical specialists using Google Places API"""
        try:
            # Construct the search query
            query = f"{specialist_type} doctor near {location}" if location else f"{specialist_type} doctor"
            
            # Make request to Places API
            params = {
                'query': query,
                'key': self.places_api_key,
                'type': 'doctor'
            }
            
            response = requests.get(PLACES_API_URL, params=params)
            response.raise_for_status()
            
            results = response.json().get('results', [])
            
            if not results:
                return None
                
            # Get the first result (highest ranked)
            top_result = results[0]
            return {
                'name': top_result.get('name'),
                'address': top_result.get('formatted_address'),
                'place_id': top_result.get('place_id')
            }
            
        except Exception as e:
            logger.error(f"Error finding specialist: {str(e)}")
            return None

    def setup_model(self):
        """Initialize the Gemini model with API key"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('models/gemini-2.0-flash')
            logger.info("Successfully initialized Gemini model")
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}")
            raise

    def generate_response(self, message):
        """Generate a response using the Gemini model"""
        try:
            logger.info("Sending request to Gemini API")
            
            structured_prompt = """You are an AI-powered medical assistant, designed to help users understand their symptoms and suggest possible medical conditions. Your responses should be concise, direct, and professional, without unnecessary elaboration. You do not provide official diagnoses or medical advice but instead guide users towards potential concerns and recommend a relevant medical specialist or general physician.

If the user describes symptoms, always ask them to rate the severity on a scale of 1-10.

When the user provides a pain/severity rating:
- For ratings lower than 6, recommend a general physician first unless the symptoms clearly indicate a specialist is needed
- For ratings 6 and above, recommend appropriate specialists based on the symptoms
- For cases that are common symptoms like headaches or runny noses unless the symptoms are incredibly intense, recommend them to a general physician or urgent care center

If the user asks for a specialist recommendation or if your response includes recommending a specialist:
1. Clearly specify the type of specialist needed (e.g., "cardiologist", "dermatologist", "general physician")
2. Start that line with "FIND_SPECIALIST:" followed by the specialist type
3. Keep it as a separate line in your response

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

            # Process the response to check for specialist recommendations
            response_text = response.text
            specialist_line = None
            
            for line in response_text.split('\n'):
                if line.startswith('FIND_SPECIALIST:'):
                    specialist_type = line.replace('FIND_SPECIALIST:', '').strip()
                    specialist_info = self.find_nearby_specialist(specialist_type)
                    if specialist_info:
                        specialist_line = f"\n\nRecommended {specialist_type}:\n" \
                                       f"Name: {specialist_info['name']}\n" \
                                       f"Address: {specialist_info['address']}"
                    break
            
            final_response = response_text.replace(line, '') if specialist_line else response_text
            if specialist_line:
                final_response += specialist_line
            
            logger.info("Successfully generated response from Gemini")
            return final_response

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