import React from 'react';
import "./Home.css"

function Home() {
  return (
    <div className="about-container">
      
      <div className="about-section">
        <h1 className="page-title">Local Cleric</h1>
        <h2>Our Mission</h2>
        <p>
          At Local Cleric, we’re redefining how you manage your health and schedule. By combining the power of <strong>AI-driven insights</strong> with intuitive organizational tools, we aim to simplify your daily life, boost productivity, and empower you to make smarter decisions—all in one seamless platform.
        </p>
      </div>

      <div className="about-section">
        <h2>Key Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <h3>AI Chat Assistant</h3>
            <p>
            Powered by Google's Gemini AI, our chatbot offers intelligent, real-time assistance for your health and scheduling needs. Describe your symptoms for personalized doctor recommendations, and get help with appointment scheduling all in a simple, conversational interface.
            </p>
          </div>
          
          <div className="feature-card">
            <h3>Event Management</h3>
            <p>
            Manage your schedule effortlessly with our intuitive calendar. Add or delete events, and let the AI handle appointments and reminders for you.
            </p>
          </div>
          
          <div className="feature-card">
            <h3>Cloud Storage</h3>
            <p>
            Securely store and access your data with <strong>Firebase</strong>, ensuring it’s always safe, synchronized, and ready when you need it.
            </p>
          </div>
          
          <div className="feature-card">
            <h3>User Authentication</h3>
            <p>
              Protect your account with **robust security features** powered by <strong>Google and Firebase</strong>. Enjoy secure logins and end-to-end encryption.
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