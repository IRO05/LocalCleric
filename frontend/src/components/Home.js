import React from 'react';

function Home() {
  return (
    <div>
      <h1 className="page-title">Welcome to Local Cleric</h1>
      <div className="section">
        <h2>Your Personal AI Assistant</h2>
        <p>
          Local Cleric is your intelligent companion, combining advanced chatbot capabilities 
          with helpful organizational tools. Navigate through our features using the menu above.
        </p>
      </div>
      <div className="section">
        <h2>Features</h2>
        <ul style={{ listStyle: 'none', padding: '1rem' }}>
          <li>✨ AI-Powered Chat Assistant</li>
          <li>📅 Event Calendar</li>
          <li>🔒 Secure Authentication</li>
          <li>💾 Cloud Storage Integration</li>
        </ul>
      </div>
    </div>
  );
}

export default Home;