import google.generativeai as genai
import json
import logging
import requests
import pandas as pd
from werkzeug.exceptions import BadRequest, InternalServerError
from datetime import datetime

logger = logging.getLogger(__name__)

PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

class Chatbot:
    def __init__(self, api_key, places_api_key):
        self.api_key = api_key
        self.places_api_key = places_api_key
        self.setup_model()
        self.load_dataset()
        self.user_symptoms = {}  # Store symptoms per user
        self.user_severity = {}  # Store overall severity per user
        self.last_interaction = {}  # Track last interaction time per user
        self.last_recommended_doctor = {}  # Store last recommended doctor per user

    def load_dataset(self):
        """Load and prepare the medical dataset"""
        try:
            self.df = pd.read_csv('dataset/dataset_with_specialists.csv')
            logger.info("Successfully loaded medical dataset")
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            raise

    def match_symptoms(self, user_symptoms):
        """Match user symptoms with diseases in the dataset"""
        matches = []
        user_symptoms = [s.lower() for s in user_symptoms]
        
        for _, row in self.df.iterrows():
            symptom_match_count = 0
            total_symptoms = 0
            
            for i in range(1, 18):
                symptom = row[f'symptom{i}']
                if pd.notna(symptom):
                    total_symptoms += 1
                    if symptom.lower() in user_symptoms:
                        symptom_match_count += 1
            
            if total_symptoms > 0 and symptom_match_count > 0:
                match_percentage = (symptom_match_count / total_symptoms) * 100
                if match_percentage >= 30:
                    matches.append({
                        'disease': row['disease'],
                        'specialist': row['specialist'],
                        'match_percentage': match_percentage
                    })
        
        matches.sort(key=lambda x: x['match_percentage'], reverse=True)
        return matches[:3]

    def find_nearby_specialist(self, specialist_type, location=""):
        """Find nearby medical specialists using Google Places API"""
        try:
            # Handle different types of doctor searches
            search_term = specialist_type.lower()
            if search_term in ["general physician", "general practitioner", "primary care"]:
                search_term = "family doctor"
            elif "specialist" in search_term:
                search_term = search_term.replace(" specialist", "")
            
            query = f"{search_term} doctor near {location}" if location else f"{search_term} doctor"
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

    def generate_response(self, message, user_id="default"):
        """Generate a response using the Gemini model"""
        try:
            logger.info("Sending request to Gemini API")
            self.last_interaction[user_id] = datetime.now()
            
            base_prompt = """You are a medical assistant. Keep responses under 2 sentences. For scheduling use:
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
I'll suggest possible conditions and specialists


Try any of these commands - I'm here to help!"""

                return {
                    'text': help_text,
                    'event_details': None
                }

            # Check for doctor/specialist requests
            specialist_types = ["cardiologist", "neurologist", "dermatologist", "pediatrician", "orthopedist"]
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

            # Handle non-doctor requests
            response = self.model.generate_content(prompt + message)
            if not response.text:
                raise ValueError("Empty response from Gemini")
            response_text = response.text
            
            # Check if user wants to schedule with last recommended doctor
            if any(term in message.lower() for term in ["schedule", "appointment", "book"]) and "them" in message.lower():
                if user_id in self.last_recommended_doctor:
                    doctor = self.last_recommended_doctor[user_id]
                    doctor_name = doctor['name'].split(',')[0]  # Get just the doctor/facility name
                    # Extract date and time from message
                    date = datetime.now().strftime('%Y-%m-%d')  # default to today
                    time = "9:00 AM"  # default time
                    
                    # Parse date
                    if "on" in message.lower():
                        message_parts = message.lower().split()
                        for i, word in enumerate(message_parts):
                            if word == "on" and i + 1 < len(message_parts):
                                date_str = message_parts[i + 1]
                                try:
                                    parsed_date = datetime.strptime(date_str, '%m/%d/%y')
                                    date = parsed_date.strftime('%Y-%m-%d')
                                except ValueError:
                                    pass
                    
                    # Parse time
                    message_parts = message.lower().split()
                    for i, word in enumerate(message_parts):
                        if word in ["at", "for"]:
                            if i + 1 < len(message_parts):
                                next_word = message_parts[i + 1]
                                if "pm" in next_word:
                                    hour = next_word.replace("pm", "").strip()
                                    if hour.isdigit() and 1 <= int(hour) <= 12:
                                        time = f"{int(hour)}:00 PM"
                                elif "am" in next_word:
                                    hour = next_word.replace("am", "").strip()
                                    if hour.isdigit() and 1 <= int(hour) <= 12:
                                        time = f"{int(hour)}:00 AM"
                    
                    response_text = f"I'll help you schedule an appointment with {doctor_name}.\nSCHEDULE_EVENT:\nTitle: Appointment with {doctor_name}\nDate: {date}\nTime: {time}"
            
            # Extract and store new symptoms if needed
            if self.should_ask_severity(user_id):
                symptoms, severity = self.extract_symptoms(response_text)
                if symptoms:
                    self.user_symptoms[user_id] = symptoms
                if severity:
                    self.user_severity[user_id] = severity
            
            # Match symptoms with diseases
            all_symptoms = self.user_symptoms.get(user_id, [])
            if all_symptoms:
                matches = self.match_symptoms(all_symptoms)
                if matches:
                    conditions = [match['disease'] for match in matches][:2]
                    specialists = list(set(match['specialist'] for match in matches))
                    specialist_info = self.find_nearby_specialist(specialists[0]) if specialists else None
                    
                    recommendations = f"\n\nPossible: {', '.join(conditions)}"
                    if specialist_info:
                        recommendations += f"\nNearest {specialists[0]}: {specialist_info['name']}"
                    
                    response_text += recommendations

            # Check for event scheduling
            event_details = self.parse_event_details(response_text)
            
            # Clean up response text by removing SCHEDULE_EVENT section
            if "SCHEDULE_EVENT:" in response_text:
                display_text = response_text.split("SCHEDULE_EVENT:")[0].strip()
            else:
                display_text = response_text

            return {
                'text': display_text,
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
        user_id = data.get('user_id', 'default')
        logger.info(f"Processing message for user {user_id}: {message[:50]}...")
        
        return self.generate_response(message, user_id)