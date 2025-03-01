# Local Cleric

A web application combining AI chatbot capabilities with organizational tools, built with React, Flask, and Firebase.

## Features

- AI-powered chatbot using Google's Gemini
- Event calendar management
- User authentication
- Cloud data storage
- Responsive design

## Prerequisites

- Node.js (v14 or higher)
- Python (v3.8 or higher)
- Firebase account
- Google Gemini API key

## Setup

### Configuration

1. Copy the template configuration file:
```bash
cp config/api_keys.template.json config/api_keys.json
```

2. Add your API keys to `config/api_keys.json`. This file is gitignored to protect your sensitive data:
```json
{
    "firebase": {
        "apiKey": "YOUR_FIREBASE_API_KEY",
        "authDomain": "your-app.firebaseapp.com",
        "projectId": "your-app-id",
        "storageBucket": "your-app.appspot.com",
        "messagingSenderId": "your-messaging-sender-id",
        "appId": "your-app-id"
    },
    "gemini": {
        "api_key": "YOUR_GEMINI_API_KEY"
    }
}
```

Note: Never commit your actual API keys to version control. The `api_keys.json` file is included in `.gitignore` for security.

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the Flask server:
```bash
python app.py
```

The backend will run on `http://localhost:5001` (Note: Using port 5001 to avoid conflicts with macOS AirPlay service)

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Project Structure

```
├── backend/
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── assets/
│   │   ├── App.js
│   │   ├── App.css
│   │   └── firebase.js
│   └── package.json
└── config/
    └── api_keys.json
```

## Technologies Used

- Frontend:
  - React
  - React Router
  - Firebase Authentication
  - CSS (Custom styling)

- Backend:
  - Flask
  - Google Gemini AI
  - Flask-CORS

- Database & Authentication:
  - Firebase

## Development

1. The backend API endpoints are available at:
   - POST `/api/chat` - Send messages to the chatbot
   - GET `/api/calendar` - Get calendar events

2. Firebase is used for:
   - User authentication
   - Storing user data and events

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request