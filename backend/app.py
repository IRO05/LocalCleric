from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
import os
import logging
from werkzeug.exceptions import BadRequest, InternalServerError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

try:
    # Load configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'api_keys.json')
    logger.info(f"Loading configuration from: {config_path}")
    
    with open(config_path) as f:
        config = json.load(f)

    # Validate config
    if not config.get('gemini', {}).get('api_key'):
        raise ValueError("Gemini API key not found in config")
    
    logger.info("Found Gemini API key in config")

    # Configure Gemini
    api_key = config['gemini']['api_key']
    genai.configure(api_key=api_key)
    logger.info("Configured Gemini API")
    
    # Initialize the model (using the standard model name)
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        logger.info("Successfully initialized Gemini model with v1beta API")
    except Exception as e:
        logger.error(f"Error initializing model: {str(e)}")
        raise
except Exception as e:
    logger.error(f"Startup Error: {str(e)}")
    raise

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        logger.info("Received chat request")
        
        if not request.is_json:
            logger.warning("Request is not JSON")
            raise BadRequest("Request must be JSON")

        data = request.json
        message = data.get('message')
        
        if not message:
            logger.warning("No message provided in request")
            raise BadRequest("Message is required")

        logger.info(f"Processing message: {message[:50]}...")  # Log first 50 chars of message

        # Generate response using Gemini
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

            response = model.generate_content(structured_prompt)
            
            if not response.text:
                logger.error("Received empty response from Gemini")
                raise ValueError("Empty response from Gemini")
            
            logger.info("Successfully generated response from Gemini")
            return jsonify({
                'response': response.text
            })
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            raise InternalServerError(f"Error generating response from AI model: {str(e)}")

    except BadRequest as e:
        logger.warning(f"Bad Request: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except InternalServerError as e:
        logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    # Placeholder for calendar data
    return jsonify({
        'events': []
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)