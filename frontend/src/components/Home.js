import React from 'react';
import "./Home.css"

function Home() {
  return (
    <div className="about-container">
      
      <div className="about-section">
        <h1 className="page-title">Local Cleric</h1>
        <h2>Our Mission</h2>
        <p>
          Local Cleric is designed to be your intelligent digital assistant,
          combining the power of AI with practical organizational tools to help
          streamline your daily activities and boost productivity.
        </p>
      </div>

      <div className="about-section">
        <h2>Key Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <h3>AI Chat Assistant</h3>
            <p>
              Powered by Google's Gemini AI, our chatbot provides intelligent
              responses and assistance for your queries.
            </p>
          </div>
          
          <div className="feature-card">
            <h3>Event Management</h3>
            <p>
              Keep track of your schedule with our intuitive calendar system,
              making event management simple and efficient.
            </p>
          </div>
          
          <div className="feature-card">
            <h3>Cloud Storage</h3>
            <p>
              Secure data storage powered by Firebase, ensuring your information
              is safe and accessible when you need it.
            </p>
          </div>
          
          <div className="feature-card">
            <h3>User Authentication</h3>
            <p>
              Robust security features to protect your account and personal
              information.
            </p>
          </div>
        </div>
      </div>

      <div className="about-section">
        <h2>Technology Stack</h2>
        <div className="tech-stack">
          <div className="tech-item">React</div>
          <div className="tech-item">Python Flask</div>
          <div className="tech-item">Firebase</div>
          <div className="tech-item">Google Gemini AI</div>
        </div>
      </div>
    </div>
  );
}

export default Home;