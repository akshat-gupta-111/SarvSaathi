import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  FiHome, FiSearch, FiCalendar, FiUser, FiLogOut, 
  FiMenu, FiX, FiBell, FiHeart, FiPhone, FiActivity
} from 'react-icons/fi';
import './Navbar.css';

const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setShowProfileMenu(false);
  };

  const isActive = (path) => location.pathname === path;

  const navLinks = [
    { path: '/', icon: FiHome, label: 'Home' },
    { path: '/search', icon: FiSearch, label: 'Find Doctors' },
    { path: '/symptom-checker', icon: FiActivity, label: 'Symptom Checker' },
    { path: '/appointments', icon: FiCalendar, label: 'Appointments' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <Link to="/" className="navbar-logo">
          <span className="logo-icon">🏥</span>
          <span className="logo-text">SarvSaathi</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="navbar-links desktop-only">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`nav-link ${isActive(link.path) ? 'active' : ''}`}
            >
              <link.icon className="nav-icon" />
              <span>{link.label}</span>
            </Link>
          ))}
        </div>

        {/* Right Section */}
        <div className="navbar-right">
          {/* Emergency Button */}
          <Link to="/emergency" className="emergency-btn">
            <FiPhone />
            <span className="desktop-only">Emergency</span>
          </Link>

          {isAuthenticated ? (
            <>
              {/* Notifications */}
              <button className="icon-btn notification-btn">
                <FiBell />
                <span className="notification-badge">3</span>
              </button>

              {/* Profile Dropdown */}
              <div className="profile-dropdown">
                <button 
                  className="profile-btn"
                  onClick={() => setShowProfileMenu(!showProfileMenu)}
                >
                  <div className="avatar">
                    {user?.email?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <span className="desktop-only">{user?.email?.split('@')[0]}</span>
                </button>

                {showProfileMenu && (
                  <div className="dropdown-menu">
                    <div className="dropdown-header">
                      <div className="avatar large">
                        {user?.email?.charAt(0).toUpperCase() || 'U'}
                      </div>
                      <div className="user-info">
                        <span className="user-email">{user?.email}</span>
                        <span className="user-type">{user?.user_type}</span>
                      </div>
                    </div>
                    <div className="dropdown-divider"></div>
                    <Link to="/profile" className="dropdown-item" onClick={() => setShowProfileMenu(false)}>
                      <FiUser /> My Profile
                    </Link>
                    <Link to="/appointments" className="dropdown-item" onClick={() => setShowProfileMenu(false)}>
                      <FiCalendar /> My Appointments
                    </Link>
                    <Link to="/favorites" className="dropdown-item" onClick={() => setShowProfileMenu(false)}>
                      <FiHeart /> Saved Doctors
                    </Link>
                    <div className="dropdown-divider"></div>
                    <button className="dropdown-item logout" onClick={handleLogout}>
                      <FiLogOut /> Logout
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="btn btn-outline btn-sm">Login</Link>
              <Link to="/register" className="btn btn-primary btn-sm">Sign Up</Link>
            </div>
          )}

          {/* Mobile Menu Toggle */}
          <button 
            className="mobile-menu-btn mobile-only"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <FiX /> : <FiMenu />}
          </button>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {mobileMenuOpen && (
        <div className="mobile-menu">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`mobile-nav-link ${isActive(link.path) ? 'active' : ''}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <link.icon className="nav-icon" />
              <span>{link.label}</span>
            </Link>
          ))}
          <Link
            to="/emergency"
            className="mobile-nav-link emergency"
            onClick={() => setMobileMenuOpen(false)}
          >
            <FiPhone className="nav-icon" />
            <span>Emergency</span>
          </Link>
          <Link
            to="/symptom-checker"
            className="mobile-nav-link"
            onClick={() => setMobileMenuOpen(false)}
          >
            <FiActivity className="nav-icon" />
            <span>Symptom Checker</span>
          </Link>
        </div>
      )}

      {/* Overlay for dropdown */}
      {showProfileMenu && (
        <div 
          className="dropdown-overlay" 
          onClick={() => setShowProfileMenu(false)}
        />
      )}
    </nav>
  );
};

export default Navbar;
