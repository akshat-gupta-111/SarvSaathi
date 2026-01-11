import React from 'react';
import { Link } from 'react-router-dom';
import {
  FiPhone, FiMail, FiMapPin, FiFacebook, FiTwitter,
  FiInstagram, FiLinkedin, FiHeart, FiArrowUp
} from 'react-icons/fi';
import './Footer.css';

const Footer = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="footer">
      <div className="footer-container">
        {/* Main Footer */}
        <div className="footer-main">
          {/* Brand Section */}
          <div className="footer-brand">
            <Link to="/" className="footer-logo">
              <span className="logo-icon">🏥</span>
              <span className="logo-text">SarvSaathi</span>
            </Link>
            <p className="brand-tagline">
              Your trusted healthcare companion. We connect patients with the best doctors,
              providing quality healthcare services at your fingertips.
            </p>
            <div className="social-links">
              <a href="#" className="social-link" aria-label="Facebook">
                <FiFacebook />
              </a>
              <a href="#" className="social-link" aria-label="Twitter">
                <FiTwitter />
              </a>
              <a href="#" className="social-link" aria-label="Instagram">
                <FiInstagram />
              </a>
              <a href="#" className="social-link" aria-label="LinkedIn">
                <FiLinkedin />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div className="footer-links">
            <h4>Quick Links</h4>
            <ul>
              <li><Link to="/">Home</Link></li>
              <li><Link to="/doctors">Find Doctors</Link></li>
              <li><Link to="/symptom-checker">Symptom Checker</Link></li>
              <li><Link to="/emergency">Emergency</Link></li>
              <li><Link to="/profile">My Profile</Link></li>
            </ul>
          </div>

          {/* Services */}
          <div className="footer-links">
            <h4>Services</h4>
            <ul>
              <li><Link to="/doctors">Book Appointment</Link></li>
              <li><Link to="/symptom-checker">AI Health Check</Link></li>
              <li><Link to="/emergency">Emergency Services</Link></li>
              <li><a href="#">Video Consultation</a></li>
              <li><a href="#">Health Records</a></li>
            </ul>
          </div>

          {/* Contact Info */}
          <div className="footer-contact">
            <h4>Contact Us</h4>
            <ul>
              <li>
                <FiMapPin className="contact-icon" />
                <span>123 Healthcare Lane, Medical District, New Delhi - 110001</span>
              </li>
              <li>
                <FiPhone className="contact-icon" />
                <span>+91 11 2345 6789</span>
              </li>
              <li>
                <FiMail className="contact-icon" />
                <span>support@sarvsaathi.com</span>
              </li>
            </ul>
            <div className="emergency-contact">
              <span className="emergency-label">24/7 Emergency</span>
              <a href="tel:102" className="emergency-number">102</a>
            </div>
          </div>
        </div>

        {/* Footer Bottom */}
        <div className="footer-bottom">
          <div className="footer-bottom-content">
            <p className="copyright">
              © {new Date().getFullYear()} SarvSaathi. All rights reserved. Made with <FiHeart className="heart-icon" /> in India
            </p>
            <div className="footer-bottom-links">
              <a href="#">Privacy Policy</a>
              <a href="#">Terms of Service</a>
              <a href="#">Sitemap</a>
            </div>
          </div>
        </div>
      </div>

      {/* Back to Top Button */}
      <button className="back-to-top" onClick={scrollToTop} aria-label="Back to top">
        <FiArrowUp />
      </button>
    </footer>
  );
};

export default Footer;
