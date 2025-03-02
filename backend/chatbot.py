import google.generativeai as genai
import json
import logging
import requests
from werkzeug.exceptions import BadRequest, InternalServerError
from datetime import datetime

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

    def parse_event_details(self, text):
        """Parse event details from AI response"""
        try:
            if "SCHEDULE_EVENT:" not in text:
                return None

            event_section = text.split("SCHEDULE_EVENT:")[1].strip()
            event_lines = event_section.split("\n")
            event_details = {}

            for line in event_lines:
                if "Title:" in line:
                    event_details['title'] = line.split("Title:")[1].strip()
                elif "Date:" in line:
                    event_details['date'] = line.split("Date:")[1].strip()
                elif "Time:" in line:
                    event_details['time'] = line.split("Time:")[1].strip()

            if 'title' in event_details and 'date' in event_details:
                return event_details
            return None

        except Exception as e:
            logger.error(f"Error parsing event details: {str(e)}")
            return None

    def generate_response(self, message):
        """Generate a response using the Gemini model"""
        try:
            logger.info("Sending request to Gemini API")
            
            structured_prompt = """You are an AI-powered medical assistant, designed to help users understand their symptoms and suggest possible medical conditions. You can also help schedule appointments and events. Your responses should be concise, direct, and professional.

For medical inquiries:
1. Ask users to rate symptoms on a scale of 1-10
2. Recommend specialists when needed using "FIND_SPECIALIST:" prefix
3. Guide users to appropriate medical professionals
4. Remind users to seek emergency care (911) for severe symptoms

For scheduling requests:
1. If the user wants to schedule something, format your response with "SCHEDULE_EVENT:" followed by:
   Title: [Event title]
   Date: [YYYY-MM-DD format]
   Time: [HH:MM format in 24-hour time]
2. Be specific about dates and times
3. If the request is vague, ask for clarification about timing
4. For medical appointments, include the type of appointment in the title

Example scheduling response:
"I'll help you schedule that appointment.

SCHEDULE_EVENT:
Title: Follow-up with Dr. Smith
Date: 2025-03-15
Time: 14:30"

Remember:
1. Maintain a professional tone
2. Be concise and direct
3. For medical queries, don't provide diagnoses
4. For scheduling, always use the specified format
5. Ask for clarification if timing is unclear

User's message: """ + message

            response = self.model.generate_content(structured_prompt)
            
            if not response.text:
                logger.error("Received empty response from Gemini")
                raise ValueError("Empty response from Gemini")

            # Process the response
            response_text = response.text
            
            # Check for specialist recommendation
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

            # Check for event scheduling
            event_details = self.parse_event_details(response_text)
            
            # Clean up response and add additional information
            final_response = response_text
            if specialist_line:
                final_response = response_text.replace(line, '') + specialist_line
            
            return {
                'text': final_response,
                'event_details': event_details
            }

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