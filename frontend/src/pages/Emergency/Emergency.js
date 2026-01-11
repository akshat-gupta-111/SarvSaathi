import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { emergencyAPI } from '../../api';
import { toast } from 'react-toastify';
import {
  FiAlertTriangle, FiPhone, FiMapPin, FiNavigation, FiPlus,
  FiEdit2, FiTrash2, FiX, FiCheck, FiShare2, FiClock,
  FiHeart, FiShield, FiAlertCircle, FiPhoneCall, FiUsers
} from 'react-icons/fi';
import './Emergency.css';

const Emergency = () => {
  const { user, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('sos');
  const [sosActive, setSosActive] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const [location, setLocation] = useState(null);
  const [locationLoading, setLocationLoading] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [showAddContact, setShowAddContact] = useState(false);
  const [newContact, setNewContact] = useState({ name: '', phone: '', relationship: '' });
  const [nearbyHospitals, setNearbyHospitals] = useState([]);

  // Emergency numbers
  const emergencyNumbers = [
    { name: 'Ambulance', number: '102', icon: '🚑', color: '#EF4444' },
    { name: 'Police', number: '100', icon: '👮', color: '#3B82F6' },
    { name: 'Fire', number: '101', icon: '🚒', color: '#F59E0B' },
    { name: 'Women Helpline', number: '1091', icon: '👩', color: '#EC4899' },
    { name: 'Emergency', number: '112', icon: '🆘', color: '#8B5CF6' },
    { name: 'Child Helpline', number: '1098', icon: '👶', color: '#10B981' },
  ];

  // Mock nearby hospitals (TODO: integrate with real hospital API)
  const mockHospitals = [
    { id: 1, name: 'Apollo Hospital', distance: '1.2 km', time: '5 min', phone: '+91 11 2692 5858', address: 'Sarita Vihar, Delhi', hasEmergency: true },
    { id: 2, name: 'Max Healthcare', distance: '2.5 km', time: '8 min', phone: '+91 11 2651 5050', address: 'Saket, Delhi', hasEmergency: true },
    { id: 3, name: 'Fortis Hospital', distance: '3.8 km', time: '12 min', phone: '+91 11 4277 6222', address: 'Okhla, Delhi', hasEmergency: true },
    { id: 4, name: 'AIIMS', distance: '5.2 km', time: '18 min', phone: '+91 11 2658 8500', address: 'Ansari Nagar, Delhi', hasEmergency: true },
  ];

  useEffect(() => {
    const fetchEmergencyContacts = async () => {
      if (isAuthenticated) {
        try {
          const response = await emergencyAPI.getEmergencyContacts();
          setContacts(response.data || []);
        } catch (error) {
          console.error('Error fetching emergency contacts:', error);
          setContacts([]);
        }
      } else {
        setContacts([]);
      }
    };
    
    fetchEmergencyContacts();
    setNearbyHospitals(mockHospitals);
    getCurrentLocation();
  }, [isAuthenticated]);

  // Countdown for SOS
  useEffect(() => {
    let timer;
    if (sosActive && countdown > 0) {
      timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    } else if (sosActive && countdown === 0) {
      triggerEmergency();
    }
    return () => clearTimeout(timer);
  }, [sosActive, countdown]);

  const getCurrentLocation = () => {
    setLocationLoading(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
          setLocationLoading(false);
        },
        (error) => {
          console.error('Location error:', error);
          setLocationLoading(false);
          toast.error('Unable to get your location');
        }
      );
    } else {
      setLocationLoading(false);
      toast.error('Geolocation is not supported');
    }
  };

  const handleSOSPress = () => {
    setSosActive(true);
    setCountdown(5);
  };

  const cancelSOS = () => {
    setSosActive(false);
    setCountdown(5);
  };

  const triggerEmergency = async () => {
    try {
      // Send emergency alert to backend
      if (isAuthenticated) {
        await emergencyAPI.triggerEmergency({
          location: location,
          contacts: contacts.map(c => c.phone)
        });
      }
      
      // Show success message
      toast.success('Emergency alerts sent to your contacts!', {
        icon: '🚨'
      });
      
      // Call ambulance
      window.location.href = 'tel:102';
    } catch (error) {
      console.error('Emergency trigger error:', error);
      // Still call ambulance even if API fails
      window.location.href = 'tel:102';
    }
    
    setSosActive(false);
    setCountdown(5);
  };

  const handleAddContact = () => {
    if (!newContact.name || !newContact.phone) {
      toast.error('Please fill in name and phone number');
      return;
    }
    
    const contact = {
      id: Date.now(),
      ...newContact
    };
    
    setContacts([...contacts, contact]);
    setNewContact({ name: '', phone: '', relationship: '' });
    setShowAddContact(false);
    toast.success('Emergency contact added');
  };

  const handleDeleteContact = (id) => {
    setContacts(contacts.filter(c => c.id !== id));
    toast.success('Contact removed');
  };

  const shareLocation = () => {
    if (location) {
      const url = `https://www.google.com/maps?q=${location.lat},${location.lng}`;
      if (navigator.share) {
        navigator.share({
          title: 'My Emergency Location',
          text: 'I need help! Here is my location:',
          url: url
        });
      } else {
        navigator.clipboard.writeText(url);
        toast.success('Location link copied to clipboard!');
      }
    } else {
      toast.error('Location not available');
    }
  };

  return (
    <div className="emergency-page">
      {/* Emergency Header */}
      <div className="emergency-header">
        <div className="header-content">
          <h1><FiAlertTriangle /> Emergency Services</h1>
          <p>Get immediate help in case of any emergency</p>
        </div>
      </div>

      {/* SOS Button - Always Visible */}
      <div className={`sos-section ${sosActive ? 'active' : ''}`}>
        {!sosActive ? (
          <button className="sos-button" onClick={handleSOSPress}>
            <span className="sos-pulse"></span>
            <span className="sos-pulse delay"></span>
            <div className="sos-content">
              <FiAlertCircle className="sos-icon" />
              <span className="sos-text">SOS</span>
              <span className="sos-subtext">Press for Emergency</span>
            </div>
          </button>
        ) : (
          <div className="sos-countdown">
            <div className="countdown-circle">
              <span className="countdown-number">{countdown}</span>
              <span className="countdown-text">Alerting in...</span>
            </div>
            <p className="countdown-message">
              Emergency services will be contacted automatically
            </p>
            <button className="cancel-sos-btn" onClick={cancelSOS}>
              <FiX /> Cancel
            </button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="emergency-tabs">
        <button 
          className={`tab-btn ${activeTab === 'sos' ? 'active' : ''}`}
          onClick={() => setActiveTab('sos')}
        >
          <FiPhone /> Quick Call
        </button>
        <button 
          className={`tab-btn ${activeTab === 'hospitals' ? 'active' : ''}`}
          onClick={() => setActiveTab('hospitals')}
        >
          <FiMapPin /> Nearby Hospitals
        </button>
        <button 
          className={`tab-btn ${activeTab === 'contacts' ? 'active' : ''}`}
          onClick={() => setActiveTab('contacts')}
        >
          <FiUsers /> My Contacts
        </button>
      </div>

      {/* Tab Content */}
      <div className="emergency-content">
        {/* Quick Call Tab */}
        {activeTab === 'sos' && (
          <div className="quick-call-tab">
            <h2>Emergency Helplines</h2>
            <div className="helplines-grid">
              {emergencyNumbers.map((item, idx) => (
                <a 
                  key={idx}
                  href={`tel:${item.number}`}
                  className="helpline-card"
                  style={{ '--accent-color': item.color }}
                >
                  <span className="helpline-icon">{item.icon}</span>
                  <div className="helpline-info">
                    <span className="helpline-name">{item.name}</span>
                    <span className="helpline-number">{item.number}</span>
                  </div>
                  <FiPhoneCall className="call-icon" />
                </a>
              ))}
            </div>

            {/* Location Card */}
            <div className="location-card">
              <div className="location-header">
                <h3><FiNavigation /> Your Location</h3>
                <button className="refresh-btn" onClick={getCurrentLocation}>
                  {locationLoading ? 'Getting...' : 'Refresh'}
                </button>
              </div>
              {location ? (
                <div className="location-info">
                  <p className="coordinates">
                    📍 {location.lat.toFixed(6)}, {location.lng.toFixed(6)}
                  </p>
                  <button className="share-location-btn" onClick={shareLocation}>
                    <FiShare2 /> Share My Location
                  </button>
                </div>
              ) : (
                <p className="no-location">
                  {locationLoading ? 'Getting your location...' : 'Location not available'}
                </p>
              )}
            </div>

            {/* First Aid Tips */}
            <div className="first-aid-section">
              <h3><FiHeart /> Quick First Aid Tips</h3>
              <div className="tips-grid">
                <div className="tip-card">
                  <span className="tip-icon">🫀</span>
                  <h4>Heart Attack</h4>
                  <p>Call 102, chew aspirin if available, loosen tight clothing</p>
                </div>
                <div className="tip-card">
                  <span className="tip-icon">🩸</span>
                  <h4>Severe Bleeding</h4>
                  <p>Apply firm pressure with clean cloth, elevate the wound</p>
                </div>
                <div className="tip-card">
                  <span className="tip-icon">🔥</span>
                  <h4>Burns</h4>
                  <p>Cool with running water for 10 min, don't apply ice</p>
                </div>
                <div className="tip-card">
                  <span className="tip-icon">😵</span>
                  <h4>Unconscious</h4>
                  <p>Check breathing, place in recovery position, call 102</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Nearby Hospitals Tab */}
        {activeTab === 'hospitals' && (
          <div className="hospitals-tab">
            <div className="hospitals-header">
              <h2>Nearby Emergency Hospitals</h2>
              <button className="refresh-btn" onClick={getCurrentLocation}>
                <FiNavigation /> Update Location
              </button>
            </div>

            <div className="hospitals-list">
              {nearbyHospitals.map(hospital => (
                <div key={hospital.id} className="hospital-card">
                  <div className="hospital-left">
                    <div className="hospital-icon">🏥</div>
                  </div>
                  <div className="hospital-info">
                    <div className="hospital-name-row">
                      <h3>{hospital.name}</h3>
                      {hospital.hasEmergency && (
                        <span className="emergency-badge">24/7 Emergency</span>
                      )}
                    </div>
                    <p className="hospital-address">{hospital.address}</p>
                    <div className="hospital-meta">
                      <span><FiMapPin /> {hospital.distance}</span>
                      <span><FiClock /> {hospital.time}</span>
                    </div>
                  </div>
                  <div className="hospital-actions">
                    <a href={`tel:${hospital.phone}`} className="call-hospital-btn">
                      <FiPhone /> Call
                    </a>
                    <a 
                      href={`https://www.google.com/maps/search/${encodeURIComponent(hospital.name + ' ' + hospital.address)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="directions-btn"
                    >
                      <FiNavigation /> Directions
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Emergency Contacts Tab */}
        {activeTab === 'contacts' && (
          <div className="contacts-tab">
            <div className="contacts-header">
              <h2>Emergency Contacts</h2>
              <button className="add-contact-btn" onClick={() => setShowAddContact(true)}>
                <FiPlus /> Add Contact
              </button>
            </div>

            <p className="contacts-info">
              <FiShield /> These contacts will be notified when you trigger an SOS alert
            </p>

            {contacts.length === 0 ? (
              <div className="no-contacts">
                <FiUsers className="no-contacts-icon" />
                <h3>No Emergency Contacts</h3>
                <p>Add contacts who should be notified in case of emergency</p>
                <button className="add-first-btn" onClick={() => setShowAddContact(true)}>
                  <FiPlus /> Add Your First Contact
                </button>
              </div>
            ) : (
              <div className="contacts-list">
                {contacts.map(contact => (
                  <div key={contact.id} className="contact-card">
                    <div className="contact-avatar">
                      {contact.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="contact-info">
                      <h4>{contact.name}</h4>
                      <p className="contact-phone">{contact.phone}</p>
                      {contact.relationship && (
                        <span className="contact-relation">{contact.relationship}</span>
                      )}
                    </div>
                    <div className="contact-actions">
                      <a href={`tel:${contact.phone}`} className="quick-call-btn">
                        <FiPhone />
                      </a>
                      <button 
                        className="delete-contact-btn"
                        onClick={() => handleDeleteContact(contact.id)}
                      >
                        <FiTrash2 />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Add Contact Modal */}
            {showAddContact && (
              <div className="modal-overlay" onClick={() => setShowAddContact(false)}>
                <div className="add-contact-modal" onClick={e => e.stopPropagation()}>
                  <div className="modal-header">
                    <h3>Add Emergency Contact</h3>
                    <button className="close-modal" onClick={() => setShowAddContact(false)}>
                      <FiX />
                    </button>
                  </div>
                  <div className="modal-body">
                    <div className="form-group">
                      <label>Name *</label>
                      <input
                        type="text"
                        placeholder="Contact name"
                        value={newContact.name}
                        onChange={e => setNewContact({...newContact, name: e.target.value})}
                      />
                    </div>
                    <div className="form-group">
                      <label>Phone Number *</label>
                      <input
                        type="tel"
                        placeholder="+91 98765 43210"
                        value={newContact.phone}
                        onChange={e => setNewContact({...newContact, phone: e.target.value})}
                      />
                    </div>
                    <div className="form-group">
                      <label>Relationship</label>
                      <select
                        value={newContact.relationship}
                        onChange={e => setNewContact({...newContact, relationship: e.target.value})}
                      >
                        <option value="">Select relationship</option>
                        <option value="Spouse">Spouse</option>
                        <option value="Parent">Parent</option>
                        <option value="Sibling">Sibling</option>
                        <option value="Child">Child</option>
                        <option value="Friend">Friend</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
                  <div className="modal-footer">
                    <button className="cancel-btn" onClick={() => setShowAddContact(false)}>
                      Cancel
                    </button>
                    <button className="save-contact-btn" onClick={handleAddContact}>
                      <FiCheck /> Add Contact
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Emergency;
