import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';
const logo = require("../assets/localClericLogo.png")

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <Link to="/">
          <img src={logo} alt="Logo" className="logo" />
        </Link>
      </div>
      <div className="navbar-links">
        <Link to="/" className="nav-link">Home</Link>
        <Link to="/calendar" className="nav-link">Calendar</Link>
        <Link to="/chatbot" className="nav-link">Chat Bot</Link>
        <Link to="/signin" className="nav-link">Sign Up/Log In</Link>
      </div>
    </nav>
  );
}

export default Navbar;