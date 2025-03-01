import React, { useState } from 'react';
import './SignIn.css';

function SignIn() {
  const [isSignIn, setIsSignIn] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    // Firebase authentication will be implemented here
    console.log('Form submitted:', formData);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">{isSignIn ? 'Sign In' : 'Sign Up'}</h1>
        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            className="auth-input"
            required
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            className="auth-input"
            required
          />
          {!isSignIn && (
            <input
              type="password"
              name="confirmPassword"
              placeholder="Confirm Password"
              value={formData.confirmPassword}
              onChange={handleChange}
              className="auth-input"
              required
            />
          )}
          <button type="submit" className="auth-button">
            {isSignIn ? 'Sign In' : 'Sign Up'}
          </button>
        </form>
        <p className="auth-switch">
          {isSignIn ? "Don't have an account? " : "Already have an account? "}
          <button
            className="switch-button"
            onClick={() => setIsSignIn(!isSignIn)}
          >
            {isSignIn ? 'Sign Up' : 'Sign In'}
          </button>
        </p>
      </div>
    </div>
  );
}

export default SignIn;