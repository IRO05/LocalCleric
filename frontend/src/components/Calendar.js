import React, { useState, useEffect, useCallback } from 'react';
import { db as getDb, auth } from '../firebase';
import {
  collection,
  addDoc,
  getDocs,
  deleteDoc,
  doc,
  query,
  orderBy,
  limit,
  startAfter,
  onSnapshot,
  where,
  Timestamp
} from 'firebase/firestore';
import { onAuthStateChanged } from 'firebase/auth';
import { useNavigate } from 'react-router-dom';
import './Calendar.css';

function Calendar() {
  const [events, setEvents] = useState([]);
  const [newEvent, setNewEvent] = useState({ title: '', date: '', time: '' });
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [lastVisible, setLastVisible] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const EVENTS_PER_PAGE = 10;
  const navigate = useNavigate();

  // Retry logic for Firestore operations
  const retryOperation = async (operation, maxAttempts = 3) => {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        console.log(`Attempt ${attempt} failed:`, error);
        if (attempt === maxAttempts) throw error;
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  };

  // Function to load events with real-time updates
  const subscribeToEvents = useCallback(async (currentUser) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    console.log('Setting up events subscription for user:', currentUser.uid);

    try {
      const eventsRef = collection(getDb(), 'users', currentUser.uid, 'events');
      console.log('Collection reference created:', eventsRef.path);

      // First try to get a single document to test permissions with retry
      await retryOperation(async () => {
        const testQuery = query(
          eventsRef,
          limit(1)
        );
        
        await getDocs(testQuery);
        console.log('Permission check passed');
      });

      // If we get here, we have permission, so proceed with the actual query
      // Create a query for all events, ordered by date
      const eventsQuery = query(
        eventsRef,
        orderBy('date', 'asc'),
        limit(EVENTS_PER_PAGE)
      );

      console.log('Query created:', {
        path: eventsRef.path,
        conditions: {
          orderBy: 'date',
          limit: EVENTS_PER_PAGE
        }
      });

      console.log('Setting up snapshot listener with query:', {
        path: eventsRef.path,
        conditions: {
          dateFrom: today.toISOString(),
          orderBy: 'date',
          limit: EVENTS_PER_PAGE
        }
      });

      // Set up snapshot listener with error handling
      const unsubscribe = onSnapshot(eventsQuery, (snapshot) => {
        console.log('Snapshot received:', {
          empty: snapshot.empty,
          size: snapshot.size,
          docs: snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data(),
            date: doc.data().date.toDate().toISOString()
          }))
        });

        const loadedEvents = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));

        console.log('Loaded events:', loadedEvents);
        setEvents(loadedEvents);
        setLastVisible(snapshot.docs[snapshot.docs.length - 1]);
        setHasMore(snapshot.docs.length === EVENTS_PER_PAGE);
        setLoading(false);
      }, (err) => {
        console.error('Error in snapshot:', err);
        setError('Error loading events: ' + err.message);
        setLoading(false);
      });

      return unsubscribe;
    } catch (err) {
      console.error('Error in events setup:', err);
      setError('Error accessing events: ' + err.message);
      setLoading(false);
      return () => {}; // Return empty cleanup function
    }
  }, []);

  useEffect(() => {
    console.log('Calendar component mounting');

    if (!auth) {
      console.error('Auth not initialized');
      setError('Unable to connect to the authentication service');
      setLoading(false);
      return;
    }

    try {
      getDb();
    } catch (error) {
      console.error('Database not initialized:', error);
      setError('Unable to connect to the database service');
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      console.log('Auth state changed:', {
        isAuthenticated: !!currentUser,
        userId: currentUser?.uid
      });

      if (!currentUser) {
        navigate('/signin');
        return;
      }

      setUser(currentUser);
      let eventsUnsubscribe;

      subscribeToEvents(currentUser)
        .then(unsubscribe => {
          eventsUnsubscribe = unsubscribe;
        })
        .catch(err => {
          console.error('Failed to subscribe to events:', err);
          setError('Failed to load events: ' + err.message);
        });

      return () => {
        if (eventsUnsubscribe) {
          eventsUnsubscribe();
        }
      };
    });

    return () => {
      unsubscribe();
    };
  }, [navigate, subscribeToEvents]);

  // Load more events
  const loadMoreEvents = async () => {
    if (!user || !lastVisible || !hasMore || loadingMore) return;

    setLoadingMore(true);
    try {
      const moreEventsQuery = query(
        collection(getDb(), 'users', user.uid, 'events'),
        orderBy('date'),
        startAfter(lastVisible),
        limit(EVENTS_PER_PAGE)
      );

      const snapshot = await getDocs(moreEventsQuery);
      const moreEvents = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      setEvents(prevEvents => [...prevEvents, ...moreEvents]);
      setLastVisible(snapshot.docs[snapshot.docs.length - 1]);
      setHasMore(snapshot.docs.length === EVENTS_PER_PAGE);
    } catch (err) {
      console.error('Error loading more events:', err);
      setError('Error loading more events');
    } finally {
      setLoadingMore(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newEvent.title || !newEvent.date || !user) return;

    try {
      // Create date object and set to midnight local time
      const [year, month, day] = newEvent.date.split('-').map(Number);
      const eventDate = new Date(year, month - 1, day); // month is 0-based
      if (isNaN(eventDate.getTime())) {
        throw new Error('Invalid date format');
      }
      eventDate.setHours(0, 0, 0, 0); // Set to midnight local time

      const eventData = {
        title: newEvent.title,
        date: Timestamp.fromDate(eventDate), // Now correctly preserves the local date
        time: newEvent.time || '',
        createdAt: Timestamp.now(),
        userId: user.uid,
        aiScheduled: false
      };

      console.log('Creating event with data:', {
        ...eventData,
        date: eventData.date.toDate().toISOString()
      });

      console.log('Adding new event with data:', eventData);
      
      await retryOperation(async () => {
        const eventsRef = collection(getDb(), 'users', user.uid, 'events');
        const docRef = await addDoc(eventsRef, eventData);
        console.log('Event added successfully with ID:', docRef.id);
      });
      
      setNewEvent({ title: '', date: '', time: '' });
    } catch (error) {
      console.error('Error adding event:', error);
      setError(`Error adding event: ${error.message}`);
    }
  };

  const deleteEvent = async (id) => {
    if (!user) return;
    
    try {
      await retryOperation(async () => {
        await deleteDoc(doc(getDb(), 'users', user.uid, 'events', id));
        console.log('Event deleted successfully:', id);
      });
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
            <button
              type="submit"
              className="add-event-button"
              disabled={loading}
            >
              {loading ? 'Adding...' : 'Add Event'}
            </button>
          </form>
        </div>

        <div className="events-list-section">
          <h2>Upcoming Events</h2>
          {loading ? (
            <p className="loading">Loading events...</p>
          ) : events.length === 0 ? (
            <p className="no-events">No upcoming events scheduled</p>
          ) : (
            <>
              <div className="events-list">
                {events.map(event => (
                  <div key={event.id} className="event-card">
                    <div className="event-info">
                      <h3>{event.title}</h3>
                      <p>Date: {event.date.toDate().toLocaleDateString()}</p>
                      {event.time && (
                        <p>Time: {
                          (() => {
                            try {
                              // Handle both 24-hour format and already formatted times
                              if (event.time.includes('AM') || event.time.includes('PM')) {
                                return event.time;
                              }
                              return new Date(`2000-01-01T${event.time}`).toLocaleTimeString('en-US', {
                                hour: 'numeric',
                                minute: '2-digit',
                                hour12: true
                              });
                            } catch (e) {
                              return event.time; // Fallback to original time string if parsing fails
                            }
                          })()
                        }</p>
                      )}
                      {event.aiScheduled && (
                        <span className="ai-badge">AI Scheduled</span>
                      )}
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
              {hasMore && (
                <button
                  onClick={loadMoreEvents}
                  className="load-more-button"
                  disabled={loadingMore}
                >
                  {loadingMore ? 'Loading...' : 'Load More Events'}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default Calendar;