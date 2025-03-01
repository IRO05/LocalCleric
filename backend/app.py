from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import logging
from werkzeug.exceptions import BadRequest
from chatbot import Chatbot

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
    if not config.get('google_places', {}).get('api_key'):
        raise ValueError("Google Places API key not found in config")
    
    # Initialize chatbot
    chatbot = Chatbot(config['gemini']['api_key'], config['google_places']['api_key'])
    
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

        response_text = chatbot.process_chat_request(request.json)
        return jsonify({'response': response_text})

    except BadRequest as e:
        logger.warning(f"Bad Request: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    # Placeholder for calendar data
    return jsonify({
        'events': []
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)