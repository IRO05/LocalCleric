from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
import os

app = Flask(__name__)
CORS(app)  

# Load configuration
with open('../config/api_keys.json') as f:
    config = json.load(f)

# Configure Gemini
genai.configure(api_key=config['gemini']['api_key'])
model = genai.GenerativeModel('gemini-pro')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        
        # Generate response using Gemini
        response = model.generate_content(message)
        
        return jsonify({
            'response': response.text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    # Placeholder for calendar data
    return jsonify({
        'events': []
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)