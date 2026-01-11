import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { doctorAPI } from '../../api';
import SearchBar from '../../components/SearchBar';
import { 
  FiStar, FiMapPin, FiClock, FiPhone, FiArrowRight, 
  FiHeart, FiTrendingUp, FiAward, FiShield, FiUsers
} from 'react-icons/fi';
import './Home.css';

// Mock data for demo (defined outside component to avoid dependency issues)
const mockDoctors = [
  {
    id: 1,
    first_name: 'Priya',
    last_name: 'Sharma',
    specialty: 'Cardiology',
    consultation_fee: 500,
    clinic_address: 'Apollo Hospital, Delhi',
    is_verified: true,
    rating: 4.8,
    reviews: 245,
  },
  {
    id: 2,
    first_name: 'Rajesh',
    last_name: 'Patel',
    specialty: 'Dermatology',
    consultation_fee: 400,
    clinic_address: 'Max Healthcare, Mumbai',
    is_verified: true,
    rating: 4.6,
    reviews: 189,
  },
  {
    id: 3,
    first_name: 'Anita',
    last_name: 'Gupta',
    specialty: 'Pediatrics',
    consultation_fee: 350,
    clinic_address: 'Fortis Hospital, Bangalore',
    is_verified: true,
    rating: 4.9,
    reviews: 312,
  },
  {
    id: 4,
    first_name: 'Vikram',
    last_name: 'Singh',
    specialty: 'Orthopedics',
    consultation_fee: 600,
    clinic_address: 'AIIMS, Delhi',
    is_verified: true,
    rating: 4.7,
    reviews: 278,
  },
];

const Home = () => {
  const { user, isAuthenticated } = useAuth();
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch verified doctors on mount
  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        const response = await doctorAPI.getVerifiedDoctors();
        setDoctors(response.data || []);
      } catch (error) {
        console.error('Error fetching doctors:', error);
        // Use mock data if API fails
        setDoctors(mockDoctors);
      } finally {
        setLoading(false);
      }
    };

    fetchDoctors();
  }, []);

  const displayDoctors = doctors.length > 0 ? doctors : mockDoctors;

  // Advertisement data
  const advertisements = [
    {
      id: 1,
      title: "50% Off on Health Checkups",
      subtitle: "Complete body checkup at partner hospitals",
      image: "🏥",
      color: "linear-gradient(135deg, #667eea, #764ba2)",
      cta: "Book Now",
      link: "/offers/health-checkup"
    },
    {
      id: 2,
      title: "Free Online Consultation",
      subtitle: "First consultation free for new users",
      image: "👨‍⚕️",
      color: "linear-gradient(135deg, #f093fb, #f5576c)",
      cta: "Consult Now",
      link: "/consult"
    },
    {
      id: 3,
      title: "Emergency Services 24/7",
      subtitle: "Ambulance at your doorstep in 15 minutes",
      image: "🚑",
      color: "linear-gradient(135deg, #4facfe, #00f2fe)",
      cta: "Call Now",
      link: "/emergency"
    },
  ];

  // Health tips
  const healthTips = [
    { icon: "💧", tip: "Drink 8 glasses of water daily" },
    { icon: "🏃", tip: "Exercise for 30 minutes everyday" },
    { icon: "😴", tip: "Get 7-8 hours of quality sleep" },
    { icon: "🥗", tip: "Eat a balanced diet with vegetables" },
  ];

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1>
            Your Health, <span className="gradient-text">Our Priority</span>
          </h1>
          <p>
            Find and book appointments with the best doctors near you. 
            Quality healthcare made accessible and affordable.
          </p>
          
          {/* Search Bar */}
          <SearchBar />
          
          {/* Stats */}
          <div className="hero-stats">
            <div className="stat">
              <span className="stat-number">500+</span>
              <span className="stat-label">Verified Doctors</span>
            </div>
            <div className="stat">
              <span className="stat-number">50+</span>
              <span className="stat-label">Partner Hospitals</span>
            </div>
            <div className="stat">
              <span className="stat-number">10K+</span>
              <span className="stat-label">Happy Patients</span>
            </div>
            <div className="stat">
              <span className="stat-number">24/7</span>
              <span className="stat-label">Emergency Support</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <div className="home-content">
        {/* Left Column - Trending Doctors/Hospitals */}
        <div className="main-column">
          {/* Quick Actions */}
          <section className="quick-actions">
            <div className="action-card">
              <div className="action-icon" style={{ background: 'rgba(79, 70, 229, 0.1)' }}>
                <FiUsers style={{ color: '#4F46E5' }} />
              </div>
              <div className="action-info">
                <h4>Find Doctors</h4>
                <p>Search by specialty or name</p>
              </div>
              <FiArrowRight />
            </div>
            <div className="action-card">
              <div className="action-icon" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
                <FiClock style={{ color: '#10B981' }} />
              </div>
              <div className="action-info">
                <h4>Book Appointment</h4>
                <p>Schedule in-clinic or online</p>
              </div>
              <FiArrowRight />
            </div>
            <div className="action-card emergency">
              <div className="action-icon" style={{ background: 'rgba(239, 68, 68, 0.1)' }}>
                <FiPhone style={{ color: '#EF4444' }} />
              </div>
              <div className="action-info">
                <h4>Emergency</h4>
                <p>Get immediate assistance</p>
              </div>
              <FiArrowRight />
            </div>
          </section>

          {/* Trending Doctors */}
          <section className="trending-section">
            <div className="section-header">
              <div className="section-title">
                <FiTrendingUp className="section-icon" />
                <h2>Trending Doctors</h2>
              </div>
              <Link to="/search" className="view-all">
                View All <FiArrowRight />
              </Link>
            </div>

            {loading ? (
              <div className="loading-grid">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="doctor-card-skeleton">
                    <div className="skeleton-avatar"></div>
                    <div className="skeleton-text"></div>
                    <div className="skeleton-text short"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="doctors-grid">
                {displayDoctors.slice(0, 4).map((doctor) => (
                  <Link 
                    key={doctor.id} 
                    to={`/doctor/${doctor.id}`}
                    className="doctor-card"
                  >
                    <div className="doctor-card-header">
                      <div className="doctor-avatar">
                        {doctor.first_name?.charAt(0)}{doctor.last_name?.charAt(0)}
                      </div>
                      <button className="favorite-btn">
                        <FiHeart />
                      </button>
                      {doctor.is_verified && (
                        <span className="verified-badge">
                          <FiShield /> Verified
                        </span>
                      )}
                    </div>
                    <div className="doctor-info">
                      <h3>Dr. {doctor.first_name} {doctor.last_name}</h3>
                      <p className="specialty">{doctor.specialty || 'General Physician'}</p>
                      <div className="doctor-meta">
                        <span className="rating">
                          <FiStar className="star-icon" />
                          {doctor.rating || '4.5'} ({doctor.reviews || '100'}+)
                        </span>
                        <span className="location">
                          <FiMapPin />
                          {doctor.clinic_address?.split(',')[0] || 'Location'}
                        </span>
                      </div>
                      <div className="doctor-footer">
                        <span className="fee">₹{doctor.consultation_fee || '500'}</span>
                        <button className="book-btn">Book Now</button>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>

          {/* Top Specialties */}
          <section className="specialties-section">
            <div className="section-header">
              <div className="section-title">
                <FiAward className="section-icon" />
                <h2>Browse by Specialty</h2>
              </div>
            </div>
            <div className="specialties-grid">
              {[
                { name: 'Cardiology', icon: '❤️', count: 45 },
                { name: 'Dermatology', icon: '🧴', count: 38 },
                { name: 'Pediatrics', icon: '👶', count: 52 },
                { name: 'Orthopedics', icon: '🦴', count: 31 },
                { name: 'Neurology', icon: '🧠', count: 28 },
                { name: 'Gynecology', icon: '👩', count: 42 },
                { name: 'Psychiatry', icon: '🧘', count: 25 },
                { name: 'General', icon: '🩺', count: 89 },
              ].map((specialty) => (
                <Link 
                  key={specialty.name}
                  to={`/search?specialty=${specialty.name}`}
                  className="specialty-card"
                >
                  <span className="specialty-icon">{specialty.icon}</span>
                  <span className="specialty-name">{specialty.name}</span>
                  <span className="specialty-count">{specialty.count} Doctors</span>
                </Link>
              ))}
            </div>
          </section>
        </div>

        {/* Right Column - Advertisements */}
        <aside className="sidebar-column">
          {/* Welcome Card (if logged in) */}
          {isAuthenticated && (
            <div className="welcome-card">
              <div className="welcome-avatar">
                {user?.email?.charAt(0).toUpperCase()}
              </div>
              <div className="welcome-info">
                <span className="welcome-greeting">Welcome back!</span>
                <span className="welcome-name">{user?.email?.split('@')[0]}</span>
              </div>
              <Link to="/profile" className="complete-profile-btn">
                Complete Profile
              </Link>
            </div>
          )}

          {/* Advertisement Cards */}
          <div className="ads-section">
            <h3 className="sidebar-title">Special Offers</h3>
            {advertisements.map((ad) => (
              <Link 
                key={ad.id}
                to={ad.link}
                className="ad-card"
                style={{ background: ad.color }}
              >
                <span className="ad-image">{ad.image}</span>
                <div className="ad-content">
                  <h4>{ad.title}</h4>
                  <p>{ad.subtitle}</p>
                  <span className="ad-cta">
                    {ad.cta} <FiArrowRight />
                  </span>
                </div>
              </Link>
            ))}
          </div>

          {/* Health Tips */}
          <div className="health-tips">
            <h3 className="sidebar-title">Daily Health Tips</h3>
            <div className="tips-list">
              {healthTips.map((tip, index) => (
                <div key={index} className="tip-item">
                  <span className="tip-icon">{tip.icon}</span>
                  <span className="tip-text">{tip.tip}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Download App */}
          <div className="download-app">
            <h4>Get the App</h4>
            <p>Download our app for a better experience</p>
            <div className="app-buttons">
              <button className="app-btn">
                <span>📱</span> iOS
              </button>
              <button className="app-btn">
                <span>🤖</span> Android
              </button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default Home;
