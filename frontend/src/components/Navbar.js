import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';
import placeholderLogo from '../assets/placeholder-logo';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <Link to="/">
          <img src={placeholderLogo} alt="Logo" className="logo" />
        </Link>
      </div>
      <div className="navbar-links">
        <Link to="/" className="nav-link">Home</Link>
        <Link to="/calendar" className="nav-link">Calendar</Link>
        <Link to="/chatbot" className="nav-link">Chat Bot</Link>
        <Link to="/signin" className="nav-link">Sign In</Link>
        <Link to="/about" className="nav-link">About</Link>
      </div>
    </nav>
  );
}

export default Navbar;