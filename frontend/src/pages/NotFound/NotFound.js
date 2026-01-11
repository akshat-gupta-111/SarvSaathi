import React from 'react';
import { Link } from 'react-router-dom';
import { FiHome, FiSearch, FiAlertCircle } from 'react-icons/fi';
import './NotFound.css';

const NotFound = () => {
  return (
    <div className="not-found-page">
      <div className="not-found-content">
        <div className="error-code">404</div>
        <div className="error-icon">
          <FiAlertCircle />
        </div>
        <h1>Page Not Found</h1>
        <p>Oops! The page you're looking for doesn't exist or has been moved.</p>
        
        <div className="not-found-actions">
          <Link to="/" className="home-btn">
            <FiHome /> Go to Home
          </Link>
          <Link to="/search" className="search-btn">
            <FiSearch /> Search Doctors
          </Link>
        </div>

        <div className="helpful-links">
          <h3>Helpful Links</h3>
          <div className="links-grid">
            <Link to="/">Home</Link>
            <Link to="/doctors">Find Doctors</Link>
            <Link to="/emergency">Emergency</Link>
            <Link to="/symptom-checker">Symptom Checker</Link>
          </div>
        </div>
      </div>

      {/* Background decoration */}
      <div className="bg-decoration">
        <div className="circle circle-1"></div>
        <div className="circle circle-2"></div>
        <div className="circle circle-3"></div>
      </div>
    </div>
  );
};

export default NotFound;
