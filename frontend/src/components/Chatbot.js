import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Chatbot.css';
import { db as getDb, auth } from '../firebase';
import { collection, addDoc, Timestamp, doc, query, orderBy, getDocs, limit } from 'firebase/firestore';
const logo = require("../assets/localClericLogo.png")

function Chatbot() {
  const [messages, setMessages] = useState([{
    text: "Welcome! I am the cleric and I shall help you with any of your medical needs, type Help to get a list of things I can do and remember! For emergencies call 911! Now how can I help you today?",
    sender: 'bot'
  }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    const initializeSession = async () => {
      try {
        const user = auth.currentUser;
        if (user) {
          const sessionsRef = collection(getDb(), 'users', user.uid, 'chatSessions');
          
          // Get the most recent session
          const q = query(sessionsRef, orderBy('startedAt', 'desc'), limit(1));
          const querySnapshot = await getDocs(q);
          
          let currentSessionId;
          
          if (querySnapshot.empty) {
            // Create new session if none exists
            const sessionDoc = await addDoc(sessionsRef, {
              startedAt: Timestamp.now(),
              userId: user.uid
            });
            currentSessionId = sessionDoc.id;
            
            // Store initial welcome message
            const messagesRef = collection(getDb(), 'users', user.uid, 'chatSessions', currentSessionId, 'messages');
            await addDoc(messagesRef, {
              text: messages[0].text,
              sender: messages[0].sender,
              timestamp: Timestamp.now()
            });
          } else {
            // Use existing session
            currentSessionId = querySnapshot.docs[0].id;
          }
          
          setSessionId(currentSessionId);
        }
      } catch (error) {
        console.error('Error initializing chat session:', error);
      }
    };

    initializeSession();
  }, []);

  const storeMessage = async (message, sender) => {
    try {
      const user = auth.currentUser;
      if (user && sessionId) {
        const messagesRef = collection(
          getDb(),
          'users',
          user.uid,
          'chatSessions',
          sessionId,
          'messages'
        );
        await addDoc(messagesRef, {
          text: message,
          sender: sender,
          timestamp: Timestamp.now()
        });
      }
    } catch (error) {
      console.error('Error storing message:', error);
    }
  };

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

      // Parse time in AM/PM format
      if (eventDetails.time) {
        const timeStr = eventDetails.time;
        const isPM = timeStr.toUpperCase().includes('PM');
        const [hoursStr, minutesStr] = timeStr.replace(/\s*(AM|PM)\s*/i, '').split(':');
        let hours = parseInt(hoursStr);
        const minutes = parseInt(minutesStr);

        // Convert to 24-hour format
        if (isPM && hours !== 12) {
          hours += 12;
        } else if (!isPM && hours === 12) {
          hours = 0;
        }

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

  useEffect(() => {
    const loadMessages = async () => {
      try {
        const user = auth.currentUser;
        if (user && sessionId) {
          const messagesRef = collection(getDb(), 'users', user.uid, 'chatSessions', sessionId, 'messages');
          const q = query(messagesRef, orderBy('timestamp', 'asc'));
          const querySnapshot = await getDocs(q);
          const loadedMessages = querySnapshot.docs.map(doc => ({
            text: doc.data().text,
            sender: doc.data().sender,
            error: doc.data().error || false
          }));

          if (loadedMessages.length > 0) {
            // For existing sessions, use all loaded messages
            setMessages(loadedMessages);
          } else {
            // For new sessions or if no messages found, ensure welcome message is present
            setMessages([{
              text: "Welcome! I am the cleric and I shall help you with any of your medical needs, type Help to get a list of things I can do and remember! For emergencies call 911! Now how can I help you today?",
              sender: 'bot'
            }]);
          }
        }
      } catch (error) {
        console.error('Error loading messages:', error);
      }
    };

    if (sessionId) {
      loadMessages();
    }
  }, [sessionId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    try {
      const user = auth.currentUser;
      if (!user) {
        throw new Error('You must be signed in to chat');
      }

      // Update UI and store message
      setMessages(prev => [...prev, { text: userMessage, sender: 'user' }]);
      await storeMessage(userMessage, 'user');

      const response = await axios.post('http://localhost:5003/api/chat', {
        message: userMessage,
        user_id: user.uid
      });

      // Handle event scheduling if suggested by the AI
      if (response.data.event_details) {
        try {
          await createEvent(response.data.event_details);
          const botResponse = response.data.response;
          const successMessage = "I've added this event to your calendar!";
          
          // Update UI first
          setMessages(prev => [
            ...prev,
            { text: botResponse, sender: 'bot' },
            { text: successMessage, sender: 'bot' }
          ]);

          // Then store in Firebase
          await Promise.all([
            storeMessage(botResponse, 'bot'),
            storeMessage(successMessage, 'bot')
          ]);
        } catch (error) {
          const botResponse = response.data.response;
          const errorMessage = `I couldn't create the event: ${error.message}`;
          
          // Update UI first
          setMessages(prev => [
            ...prev,
            { text: botResponse, sender: 'bot' },
            { text: errorMessage, sender: 'bot', error: true }
          ]);

          // Then store in Firebase
          await Promise.all([
            storeMessage(botResponse, 'bot'),
            storeMessage(errorMessage, 'bot')
          ]);
        }
      } else {
        const botResponse = response.data.response;
        
        // Update UI first
        setMessages(prev => [...prev, { text: botResponse, sender: 'bot' }]);
        
        // Then store in Firebase
        await storeMessage(botResponse, 'bot');
      }
    } catch (error) {
      console.error('Error:', error.response?.data?.error || error.message);
      const errorMessage = error.response?.data?.error || 'Sorry, I encountered an error. Please try again.';
      
      // Update UI first
      setMessages(prev => [...prev, {
        text: errorMessage,
        sender: 'bot',
        error: true
      }]);

      // Then store in Firebase
      await storeMessage(errorMessage, 'bot');
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