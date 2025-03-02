import React, { useState } from 'react';
import axios from 'axios';
import './Chatbot.css';
import { db as getDb, auth } from '../firebase';
import { collection, addDoc, Timestamp } from 'firebase/firestore';
const logo = require("../assets/localClericLogo.png")

function Chatbot() {
  const [messages, setMessages] = useState([{
    text: "Thank you for choosing your local cleric! If this is a life threatening issue please contact 911\nHow can I help you today?",
    sender: 'bot'
  }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const createEvent = async (eventDetails) => {
    try {
      const user = auth.currentUser;
      if (!user) {
        throw new Error('You must be signed in to schedule events');
      }

      // Parse the date string to ensure correct format
      const [year, month, day] = eventDetails.date.split('-').map(Number);
      const eventDate = new Date(year, month - 1, day); // month is 0-based
      
      if (isNaN(eventDate.getTime())) {
        throw new Error('Invalid date format');
      }

      // Set the time if provided
      if (eventDetails.time) {
        const [hours, minutes] = eventDetails.time.split(':').map(Number);
        eventDate.setHours(hours, minutes);
      }

      const eventData = {
        title: eventDetails.title,
        date: Timestamp.fromDate(eventDate),
        time: eventDetails.time || '',
        createdAt: Timestamp.now(),
        userId: user.uid,
        aiScheduled: true
      };

      console.log('Creating event with data:', eventData);

      const eventsRef = collection(getDb(), 'users', user.uid, 'events');
      const docRef = await addDoc(eventsRef, eventData);
      console.log('Event created with ID:', docRef.id);

      return true;
    } catch (error) {
      console.error('Error creating event:', error);
      throw error;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { text: userMessage, sender: 'user' }]);
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:5003/api/chat', {
        message: userMessage
      });

      // Handle event scheduling if suggested by the AI
      if (response.data.event_details) {
        try {
          await createEvent(response.data.event_details);
          setMessages(prev => [
            ...prev,
            { text: response.data.response, sender: 'bot' },
            { text: "I've added this event to your calendar!", sender: 'bot' }
          ]);
        } catch (error) {
          setMessages(prev => [
            ...prev,
            { text: response.data.response, sender: 'bot' },
            { text: `I couldn't create the event: ${error.message}`, sender: 'bot', error: true }
          ]);
        }
      } else {
        setMessages(prev => [...prev, { text: response.data.response, sender: 'bot' }]);
      }
    } catch (error) {
      console.error('Error:', error.response?.data?.error || error.message);
      setMessages(prev => [...prev, {
        text: error.response?.data?.error || 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        error: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      <h1 id="clerictitle" className="page-title">Approach the cleric</h1>
      <div className="chat-window">
        <img id="chatLogo" src={logo} alt="Logo" />
        <div className="messages">
          {messages.map((message, index) => (
            <div 
              key={index} 
              className={`message ${message.sender} ${message.error ? 'error' : ''}`}
            >
              {message.text}
            </div>
          ))}
          {isLoading && (
            <div className="message bot loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="chat-input"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={isLoading}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default Chatbot;