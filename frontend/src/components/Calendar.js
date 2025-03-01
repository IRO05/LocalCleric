import React, { useState } from 'react';
import './Calendar.css';

function Calendar() {
  const [events, setEvents] = useState([]);
  const [newEvent, setNewEvent] = useState({ title: '', date: '', time: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!newEvent.title || !newEvent.date) return;

    setEvents([...events, { ...newEvent, id: Date.now() }]);
    setNewEvent({ title: '', date: '', time: '' });
  };

  const deleteEvent = (id) => {
    setEvents(events.filter(event => event.id !== id));
  };

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
            />
            <input
              type="date"
              value={newEvent.date}
              onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
              className="event-input"
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
          {events.length === 0 ? (
            <p className="no-events">No events scheduled</p>
          ) : (
            <div className="events-list">
              {events
                .sort((a, b) => new Date(a.date) - new Date(b.date))
                .map(event => (
                  <div key={event.id} className="event-card">
                    <div className="event-info">
                      <h3>{event.title}</h3>
                      <p>Date: {new Date(event.date).toLocaleDateString()}</p>
                      {event.time && <p>Time: {event.time}</p>}
                    </div>
                    <button
                      onClick={() => deleteEvent(event.id)}
                      className="delete-event-button"
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