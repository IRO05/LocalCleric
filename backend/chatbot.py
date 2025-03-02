import google.generativeai as genai
import json
import logging
import requests
from werkzeug.exceptions import BadRequest, InternalServerError
from datetime import datetime
import re

logger = logging.getLogger(__name__)

PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

class Chatbot:
    def __init__(self, api_key, places_api_key):
        self.api_key = api_key
        self.places_api_key = places_api_key
        self.setup_model()
        self.user_symptoms = {}  # Store symptoms per user
        self.user_severity = {}  # Store overall severity per user
        self.last_interaction = {}  # Track last interaction time per user
        self.last_recommended_doctor = {}  # Store last recommended doctor per user
        self.awaiting_more_symptoms = {}  # Track if we're waiting for more symptoms

    def setup_model(self):
        """Initialize the Gemini model with API key"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Successfully initialized Gemini model")
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}")
            raise

    def get_specialist_for_symptoms(self, symptoms):
        """Map symptoms to appropriate medical specialists"""
        # Common symptom-to-specialist mappings
        specialist_mappings = {
            'headache': ['neurologist', 'general physician'],
            'migraine': ['neurologist'],
            'chest pain': ['cardiologist'],
            'heart': ['cardiologist'],
            'skin': ['dermatologist'],
            'rash': ['dermatologist'],
            'joint pain': ['orthopedist'],
            'bone': ['orthopedist'],
            'muscle': ['orthopedist'],
            'vision': ['ophthalmologist'],
            'eye': ['ophthalmologist'],
            'stomach': ['gastroenterologist'],
            'digestive': ['gastroenterologist'],
            'mental': ['psychiatrist'],
            'anxiety': ['psychiatrist'],
            'depression': ['psychiatrist'],
            'hormone': ['endocrinologist'],
            'diabetes': ['endocrinologist'],
            'thyroid': ['endocrinologist'],
            'pregnancy': ['obstetrician'],
            'gynecological': ['gynecologist'],
            'urinary': ['urologist'],
            'kidney': ['urologist']
        }

        recommended_specialists = set()
        for symptom in symptoms:
            symptom = symptom.lower()
            for key, specialists in specialist_mappings.items():
                if key in symptom:
                    recommended_specialists.update(specialists)

        # Default to general physician if no specific specialist is found
        if not recommended_specialists:
            recommended_specialists.add('general physician')

        return list(recommended_specialists)

    def find_nearby_specialist(self, specialist_type):
        """Find nearby medical specialists using Google Places API"""
        try:
            # Handle different types of doctor searches
            search_term = specialist_type.lower()
            if search_term in ["general physician", "general practitioner", "primary care"]:
                search_term = "family doctor"
            elif "specialist" in search_term:
                search_term = search_term.replace(" specialist", "")
            
            # Use default location (Newark, DE) for searches
            query = f"{search_term} doctor in Newark, DE"
            params = {
                'query': query,
                'key': self.places_api_key,
                'type': 'doctor',
                'location': '39.6837,-75.7497',  # Newark, DE coordinates
                'radius': '10000'  # 10km radius
            }
            
            response = requests.get(PLACES_API_URL, params=params)
            response.raise_for_status()
            results = response.json().get('results', [])
            
            if not results:
                return None
                
            top_result = results[0]
            return {
                'name': top_result.get('name'),
                'address': top_result.get('formatted_address'),
                'place_id': top_result.get('place_id')
            }
            
        except Exception as e:
            logger.error(f"Error finding specialist: {str(e)}")
            return None

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

    def extract_symptoms(self, ai_response):
        """Extract symptoms from AI response"""
        try:
            symptoms = []
            severity = None
            lines = ai_response.split('\n')
            
            for line in lines:
                if line.startswith('Symptoms:'):
                    symptoms_text = line.replace('Symptoms:', '').strip()
                    symptoms = [s.strip() for s in symptoms_text.split(',')]
                elif line.startswith('Severity:'):
                    severity = line.replace('Severity:', '').strip()
            
            return symptoms, severity
        except Exception as e:
            logger.error(f"Error extracting symptoms: {str(e)}")
            return [], None

    def should_ask_severity(self, user_id):
        """Determine if we should ask for symptom severity"""
        current_time = datetime.now()
        return (user_id not in self.last_interaction or 
                (current_time - self.last_interaction[user_id]).total_seconds() > 3600)

    def parse_time(self, message):
        """Parse time from message"""
        try:
            # Look for time pattern like "1:14pm" or "2pm"
            time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)'
            match = re.search(time_pattern, message.lower())
            
            if match:
                hour = int(match.group(1))
                minutes = int(match.group(2)) if match.group(2) else 0
                period = match.group(3).upper()
                
                # Convert to 12-hour format
                if period == "PM" and hour != 12:
                    hour += 12
                elif period == "AM" and hour == 12:
                    hour = 0
                
                return f"{hour % 12 or 12}:{minutes:02d} {period}"
            
            return "9:00 AM"  # Default time
        except Exception as e:
            logger.error(f"Error parsing time: {str(e)}")
            return "9:00 AM"

    def parse_date(self, message):
        """Parse date from message"""
        try:
            # Look for date pattern like "3/8/25"
            date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})'
            match = re.search(date_pattern, message)
            
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                year = int(match.group(3))
                
                # Convert 2-digit year to 4-digit
                if year < 100:
                    year += 2000
                
                # Validate date
                try:
                    return datetime(year, month, day).strftime('%Y-%m-%d')
                except ValueError:
                    return datetime.now().strftime('%Y-%m-%d')
            
            return datetime.now().strftime('%Y-%m-%d')  # Default to today
        except Exception as e:
            logger.error(f"Error parsing date: {str(e)}")
            return datetime.now().strftime('%Y-%m-%d')

    def generate_response(self, message, user_id="default"):
        """Generate a response using the Gemini model"""
        try:
            logger.info("Sending request to Gemini API")
            self.last_interaction[user_id] = datetime.now()
            
            base_prompt = """You are a medical assistant. Keep responses under 2 sentences. Only include SCHEDULE_EVENT if the user explicitly asks to schedule an appointment with a specific doctor. For scheduling use:
SCHEDULE_EVENT:
Title: [title]
Date: YYYY-MM-DD
Time: HH:MM

Message: """

            if self.should_ask_severity(user_id):
                prompt = base_prompt
            else:
                symptoms = ', '.join(self.user_symptoms.get(user_id, []))
                severity = self.user_severity.get(user_id, 'Not provided')
                prompt = f"Previous: {symptoms} (Severity: {severity})\n{base_prompt}"

            message_lower = message.lower().strip()
            
            # Handle greetings, thanks, and goodbyes
            greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
            thanks = ["thank you", "thanks", "appreciate it", "thank"]
            goodbyes = ["bye", "goodbye", "see you", "see ya"]
            
            if any(message_lower.startswith(greeting) for greeting in greetings):
                return {
                    'text': "Hello! How can I help you today?",
                    'event_details': None
                }
            
            if any(thank in message_lower for thank in thanks):
                return {
                    'text': "You're welcome!",
                    'event_details': None
                }
                
            if any(goodbye in message_lower for goodbye in goodbyes):
                return {
                    'text': "Goodbye! Take care!",
                    'event_details': None
                }
            
            # Handle help command first
            if message_lower == "help":
                help_text = """Here's how to use the cleric:


To find a doctor near you, try saying:
"Can you find me a general physician?"
"I need a cardiologist near me"


To schedule an appointment:
After finding a doctor, simply say:
"Schedule an appointment with them for [time] on [date]"
For example: "Schedule an appointment with them for 2:30 PM on 3/15/25"


To get medical advice:
Tell me your symptoms and rate your discomfort (1-10)
For example: "I have headache and nausea, severity is 7"
I'll ask if you have more symptoms, then suggest appropriate specialists


Try any of these commands - I'm here to help!"""

                return {
                    'text': help_text,
                    'event_details': None
                }

            # Check if we're waiting for more symptoms
            if user_id in self.awaiting_more_symptoms and self.awaiting_more_symptoms[user_id]:
                if any(word in message_lower for word in ['no', 'nope', "that's all", 'thats all', 'those are all']):
                    self.awaiting_more_symptoms[user_id] = False
                    # Get specialist recommendations based on all collected symptoms
                    all_symptoms = self.user_symptoms.get(user_id, [])
                    if all_symptoms:
                        recommended_specialists = self.get_specialist_for_symptoms(all_symptoms)
                        if recommended_specialists:
                            specialist_info = self.find_nearby_specialist(recommended_specialists[0])
                            if specialist_info:
                                self.last_recommended_doctor[user_id] = specialist_info
                                return {
                                    'text': f"Based on your symptoms, I recommend seeing a {recommended_specialists[0]}. I found one nearby: {specialist_info['name']} at {specialist_info['address']}. Would you like me to schedule an appointment?",
                                    'event_details': None
                                }
                    return {
                        'text': "I recommend seeing a general physician to evaluate your symptoms. Would you like me to find one nearby?",
                        'event_details': None
                    }
                else:
                    # Add new symptoms to the existing list
                    response = self.model.generate_content(base_prompt + message)
                    if response.text:
                        new_symptoms, new_severity = self.extract_symptoms(response.text)
                        if new_symptoms:
                            current_symptoms = self.user_symptoms.get(user_id, [])
                            self.user_symptoms[user_id] = list(set(current_symptoms + new_symptoms))
                        if new_severity:
                            self.user_severity[user_id] = new_severity
                    return {
                        'text': "I've noted those additional symptoms. Are there any other symptoms you'd like to mention?",
                        'event_details': None
                    }

            # Check for doctor/specialist requests
            specialist_types = [
                "cardiologist", "neurologist", "dermatologist", "pediatrician",
                "orthopedist", "gynecologist", "obstetrician", "psychiatrist",
                "ophthalmologist", "urologist", "endocrinologist"
            ]
            doctor_type = None

            # Check for specialists first
            for specialist in specialist_types:
                if specialist in message_lower:
                    doctor_type = specialist
                    break
            
            # Check for general doctor requests
            if not doctor_type and any(term in message_lower for term in ["doctor", "physician"]):
                doctor_type = "family doctor"

            # Handle doctor search if applicable
            if doctor_type:
                specialist_info = self.find_nearby_specialist(doctor_type)
                if specialist_info:
                    self.last_recommended_doctor[user_id] = specialist_info
                    return {
                        'text': f"I found a {doctor_type} near you: {specialist_info['name']} at {specialist_info['address']}",
                        'event_details': None
                    }
                else:
                    return {
                        'text': f"I apologize, but I couldn't find a {doctor_type} in the area. Please try again later.",
                        'event_details': None
                    }

            # Handle scheduling requests
            if any(term in message.lower() for term in ["schedule", "appointment", "book"]) and "them" in message.lower():
                if user_id in self.last_recommended_doctor:
                    doctor = self.last_recommended_doctor[user_id]
                    doctor_name = doctor['name'].split(',')[0]  # Get just the doctor/facility name
                    
                    # Parse date and time from message
                    date = self.parse_date(message)
                    time = self.parse_time(message)
                    
                    response_text = f"I'll help you schedule an appointment with {doctor_name}.\nSCHEDULE_EVENT:\nTitle: Appointment with {doctor_name}\nDate: {date}\nTime: {time}"
                    return {
                        'text': f"I'll help you schedule an appointment with {doctor_name}.",
                        'event_details': self.parse_event_details(response_text)
                    }
                else:
                    return {
                        'text': "I don't have a doctor to schedule with. Please find a doctor first using the find command.",
                        'event_details': None
                    }

            # Handle new symptoms
            response = self.model.generate_content(base_prompt + message)
            if not response.text:
                raise ValueError("Empty response from Gemini")
            
            symptoms, severity = self.extract_symptoms(response.text)
            if symptoms:
                self.user_symptoms[user_id] = symptoms
                if severity:
                    self.user_severity[user_id] = severity
                self.awaiting_more_symptoms[user_id] = True
                return {
                    'text': "I understand you're experiencing these symptoms. Are there any other symptoms you'd like to mention?",
                    'event_details': None
                }
            
            # If no symptoms found, just return the cleaned response
            display_text = response.text
            if "Message:" in display_text:
                display_text = display_text.split("Message:")[1].strip()
            display_text = display_text.replace("You are a medical assistant", "").strip()
            display_text = display_text.replace("Keep responses under 2 sentences", "").strip()

            return {
                'text': display_text,
                'event_details': None
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
        user_id = data.get('user_id', 'default')
        logger.info(f"Processing message for user {user_id}: {message[:50]}...")
        
        return self.generate_response(message, user_id)