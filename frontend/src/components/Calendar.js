import React, { useState, useEffect } from 'react';
import { db, auth } from '../firebase';
import { collection, addDoc, getDocs, deleteDoc, doc, query, orderBy } from 'firebase/firestore';
import { onAuthStateChanged } from 'firebase/auth';
import { useNavigate } from 'react-router-dom';
import './Calendar.css';

function Calendar() {
  const [events, setEvents] = useState([]);
  const [newEvent, setNewEvent] = useState({ title: '', date: '', time: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if Firebase is initialized
    if (!auth || !db) {
      setError('Unable to connect to the service');
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      try {
        if (!currentUser) {
          navigate('/signin');
          return;
        }

        setUser(currentUser);
        const eventsQuery = query(
          collection(db, 'users', currentUser.uid, 'events'),
          orderBy('date')
        );
        const querySnapshot = await getDocs(eventsQuery);
        const loadedEvents = querySnapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        setEvents(loadedEvents);
      } catch (err) {
        console.error('Error:', err);
        setError('Error loading events');
      } finally {
        setLoading(false);
      }
    });

    return () => {
      unsubscribe();
      setLoading(false);
    };
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newEvent.title || !newEvent.date || !user) return;

    try {
      const docRef = await addDoc(collection(db, 'users', user.uid, 'events'), {
        ...newEvent,
        createdAt: new Date(),
        userId: user.uid
      });
      
      setEvents([...events, { ...newEvent, id: docRef.id }]);
      setNewEvent({ title: '', date: '', time: '' });
    } catch (error) {
      console.error('Error adding event:', error);
      setError('Error adding event');
    }
  };

  const deleteEvent = async (id) => {
    if (!user) return;
    
    try {
      await deleteDoc(doc(db, 'users', user.uid, 'events', id));
      setEvents(events.filter(event => event.id !== id));
    } catch (error) {
      console.error('Error deleting event:', error);
      setError('Error deleting event');
    }
  };

  if (error) {
    return (
      <div className="calendar-container">
        <p className="error-message">{error}</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="calendar-container">
      <h1 className="page-title">Calendar</h1>
      
      <div className="calendar-grid">
        <div className="add-event-section">
          <h2>Add New Event</h2>
          <form onSubmit={handleSubmit} className="event-form">
            <input
              type="text"
              placeholder="Event Title"
              value={newEvent.title}
              onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
              className="event-input"
              required
            />
            <input
              type="date"
              value={newEvent.date}
              onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
              className="event-input"
              required
            />
            <input
              type="time"
              value={newEvent.time}
              onChange={(e) => setNewEvent({ ...newEvent, time: e.target.value })}
              className="event-input"
            />
            <button type="submit" className="add-event-button">
              Add Event
            </button>
          </form>
        </div>

        <div className="events-list-section">
          <h2>Upcoming Events</h2>
          {loading ? (
            <p className="loading">Loading events...</p>
          ) : events.length === 0 ? (
            <p className="no-events">No events scheduled</p>
          ) : (
            <div className="events-list">
              {events.map(event => (
                <div key={event.id} className="event-card">
                  <div className="event-info">
                    <h3>{event.title}</h3>
                    <p>Date: {new Date(event.date).toLocaleDateString()}</p>
                    {event.time && <p>Time: {event.time}</p>}
                  </div>
                  <button
                    onClick={() => deleteEvent(event.id)}
                    className="delete-event-button"
                    aria-label="Delete event"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Calendar;