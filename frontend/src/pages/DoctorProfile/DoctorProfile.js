import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { doctorAPI, appointmentsAPI } from '../../api';
import { toast } from 'react-toastify';
import {
  FiArrowLeft, FiStar, FiMapPin, FiClock, FiPhone, FiMail,
  FiCalendar, FiAward, FiShield, FiHeart, FiShare2, FiCheck,
  FiChevronRight, FiUser, FiMessageSquare, FiVideo, FiBriefcase
} from 'react-icons/fi';
import './DoctorProfile.css';

const DoctorProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  const [doctor, setDoctor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('about');
  const [isFavorite, setIsFavorite] = useState(false);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);

  // Generate next 7 days for date selection
  const getNextDays = () => {
    const days = [];
    const today = new Date();
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      days.push({
        date: date,
        day: date.toLocaleDateString('en-US', { weekday: 'short' }),
        dateNum: date.getDate(),
        month: date.toLocaleDateString('en-US', { month: 'short' }),
        full: date.toISOString().split('T')[0]
      });
    }
    return days;
  };

  const availableDates = getNextDays();

  // Fallback time slots (used if API doesn't return slots)
  const defaultTimeSlots = {
    morning: ['09:00 AM', '09:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM'],
    afternoon: ['02:00 PM', '02:30 PM', '03:00 PM', '03:30 PM', '04:00 PM', '04:30 PM'],
    evening: ['06:00 PM', '06:30 PM', '07:00 PM', '07:30 PM', '08:00 PM']
  };

  // Get time slots from API grouped by time period
  const getGroupedSlots = () => {
    if (availableSlots.length === 0) return defaultTimeSlots;
    
    const filtered = availableSlots.filter(slot => slot.date === selectedDate && slot.status === 'available');
    const grouped = { morning: [], afternoon: [], evening: [] };
    
    filtered.forEach(slot => {
      const hour = parseInt(slot.start_time.split(':')[0]);
      const timeStr = formatTime(slot.start_time);
      const slotData = { ...slot, displayTime: timeStr };
      
      if (hour < 12) grouped.morning.push(slotData);
      else if (hour < 17) grouped.afternoon.push(slotData);
      else grouped.evening.push(slotData);
    });
    
    return grouped;
  };

  const formatTime = (time24) => {
    const [hours, minutes] = time24.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
  };

  const timeSlots = getGroupedSlots();

  useEffect(() => {
    const fetchDoctor = async () => {
      try {
        const response = await doctorAPI.getDoctorProfile(id);
        setDoctor(response.data);
      } catch (error) {
        console.error('Error fetching doctor:', error);
        // Navigate back if doctor not found
        toast.error('Doctor not found');
        navigate('/search-doctors');
      } finally {
        setLoading(false);
      }
    };

    const fetchTimeSlots = async () => {
      setSlotsLoading(true);
      try {
        const response = await appointmentsAPI.getDoctorSlots(id);
        setAvailableSlots(response.data || []);
      } catch (error) {
        console.error('Error fetching time slots:', error);
        setAvailableSlots([]);
      } finally {
        setSlotsLoading(false);
      }
    };

    fetchDoctor();
    fetchTimeSlots();
    // Set first date as default
    setSelectedDate(availableDates[0].full);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, navigate]);

  const handleBookAppointment = async () => {
    if (!isAuthenticated) {
      toast.info('Please login to book an appointment');
      navigate('/login', { state: { from: `/doctor/${id}` } });
      return;
    }

    if (!selectedSlot) {
      toast.error('Please select a time slot');
      return;
    }

    // Check if selectedSlot is an object (real slot from API) or string (mock slot)
    const slotId = typeof selectedSlot === 'object' ? selectedSlot.id : null;
    
    if (!slotId) {
      toast.error('No available time slots. Please ask the doctor to add slots.');
      return;
    }

    setBookingLoading(true);
    try {
      const appointmentData = {
        time_slot_id: slotId,
        reason: 'Consultation'
      };

      await appointmentsAPI.bookAppointment(appointmentData);
      toast.success('Appointment booked successfully!');
      navigate('/profile');
    } catch (error) {
      console.error('Booking error:', error);
      const errorMsg = error.response?.data?.time_slot_id?.[0] || 
                      error.response?.data?.detail || 
                      error.response?.data?.error ||
                      'Failed to book appointment';
      toast.error(errorMsg);
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="doctor-profile-loading">
        <div className="loading-spinner"></div>
        <p>Loading doctor profile...</p>
      </div>
    );
  }

  if (!doctor) {
    return (
      <div className="doctor-profile-loading">
        <p>Doctor not found</p>
        <button onClick={() => navigate('/search-doctors')}>Back to Search</button>
      </div>
    );
  }

  const displayDoctor = doctor;

  return (
    <div className="doctor-profile-page">
      {/* Back Navigation */}
      <div className="profile-nav">
        <button className="back-btn" onClick={() => navigate(-1)}>
          <FiArrowLeft /> Back
        </button>
        <div className="nav-actions">
          <button 
            className={`action-btn ${isFavorite ? 'active' : ''}`}
            onClick={() => setIsFavorite(!isFavorite)}
          >
            <FiHeart />
          </button>
          <button className="action-btn">
            <FiShare2 />
          </button>
        </div>
      </div>

      <div className="profile-content">
        {/* Main Content */}
        <div className="profile-main">
          {/* Doctor Header Card */}
          <div className="doctor-header-card">
            <div className="doctor-avatar-large">
              {displayDoctor.first_name?.charAt(0)}{displayDoctor.last_name?.charAt(0)}
            </div>
            <div className="doctor-header-info">
              <div className="name-row">
                <h1>Dr. {displayDoctor.first_name} {displayDoctor.last_name}</h1>
                {displayDoctor.is_verified && (
                  <span className="verified-badge-large">
                    <FiShield /> Verified
                  </span>
                )}
              </div>
              <p className="specialty-text">{displayDoctor.specialty || 'General Physician'}</p>
              <p className="qualification-text">{displayDoctor.qualification || 'MBBS, MD'}</p>
              
              <div className="doctor-stats-row">
                <div className="stat-item">
                  <FiStar className="stat-icon star" />
                  <span className="stat-value">{displayDoctor.rating || '4.5'}</span>
                  <span className="stat-label">({displayDoctor.reviews || '100'}+ reviews)</span>
                </div>
                <div className="stat-item">
                  <FiBriefcase className="stat-icon" />
                  <span className="stat-value">{displayDoctor.experience || '10'}+ yrs</span>
                  <span className="stat-label">Experience</span>
                </div>
                <div className="stat-item">
                  <FiUser className="stat-icon" />
                  <span className="stat-value">{displayDoctor.patients_treated || '1000'}+</span>
                  <span className="stat-label">Patients</span>
                </div>
              </div>

              <div className="contact-row">
                <span className="contact-item">
                  <FiMapPin /> {displayDoctor.clinic_address?.split(',')[0] || 'Delhi'}
                </span>
                <span className="contact-item">
                  <FiClock /> Available Today
                </span>
              </div>
            </div>
            <div className="fee-section">
              <span className="fee-label">Consultation Fee</span>
              <span className="fee-amount">₹{displayDoctor.consultation_fee || '500'}</span>
            </div>
          </div>

          {/* Tabs */}
          <div className="profile-tabs">
            <button 
              className={`tab-btn ${activeTab === 'about' ? 'active' : ''}`}
              onClick={() => setActiveTab('about')}
            >
              About
            </button>
            <button 
              className={`tab-btn ${activeTab === 'services' ? 'active' : ''}`}
              onClick={() => setActiveTab('services')}
            >
              Services
            </button>
            <button 
              className={`tab-btn ${activeTab === 'reviews' ? 'active' : ''}`}
              onClick={() => setActiveTab('reviews')}
            >
              Reviews
            </button>
            <button 
              className={`tab-btn ${activeTab === 'education' ? 'active' : ''}`}
              onClick={() => setActiveTab('education')}
            >
              Education
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'about' && (
              <div className="about-tab">
                <div className="info-section">
                  <h3>About Doctor</h3>
                  <p>{displayDoctor.bio || 'A highly experienced and dedicated healthcare professional committed to providing the best care to patients.'}</p>
                </div>

                <div className="info-section">
                  <h3>Clinic Details</h3>
                  <div className="clinic-info">
                    <div className="clinic-item">
                      <FiMapPin className="clinic-icon" />
                      <div>
                        <span className="clinic-label">Address</span>
                        <span className="clinic-value">{displayDoctor.clinic_address || 'Not specified'}</span>
                      </div>
                    </div>
                    <div className="clinic-item">
                      <FiPhone className="clinic-icon" />
                      <div>
                        <span className="clinic-label">Phone</span>
                        <span className="clinic-value">{displayDoctor.phone || '+91 98765 43210'}</span>
                      </div>
                    </div>
                    <div className="clinic-item">
                      <FiMail className="clinic-icon" />
                      <div>
                        <span className="clinic-label">Email</span>
                        <span className="clinic-value">{displayDoctor.email}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="info-section">
                  <h3>Working Hours</h3>
                  <div className="working-hours">
                    <div className="hours-row">
                      <span>Mon - Fri</span>
                      <span>{displayDoctor.working_hours?.weekdays || '9:00 AM - 6:00 PM'}</span>
                    </div>
                    <div className="hours-row">
                      <span>Saturday</span>
                      <span>{displayDoctor.working_hours?.saturday || '9:00 AM - 2:00 PM'}</span>
                    </div>
                    <div className="hours-row">
                      <span>Sunday</span>
                      <span>{displayDoctor.working_hours?.sunday || 'Closed'}</span>
                    </div>
                  </div>
                </div>

                <div className="info-section">
                  <h3>Languages Spoken</h3>
                  <div className="languages">
                    {(displayDoctor.languages || ['English', 'Hindi']).map((lang, idx) => (
                      <span key={idx} className="language-tag">{lang}</span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'services' && (
              <div className="services-tab">
                <h3>Services Offered</h3>
                <div className="services-grid">
                  {(displayDoctor.services || ['General Consultation', 'Follow-up Visit', 'Health Checkup']).map((service, idx) => (
                    <div key={idx} className="service-item">
                      <FiCheck className="service-icon" />
                      <span>{service}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'reviews' && (
              <div className="reviews-tab">
                <div className="reviews-summary">
                  <div className="rating-big">
                    <span className="rating-number">{displayDoctor.rating || '4.5'}</span>
                    <div className="stars">
                      {[1, 2, 3, 4, 5].map(star => (
                        <FiStar 
                          key={star} 
                          className={star <= Math.floor(displayDoctor.rating || 4.5) ? 'filled' : ''} 
                        />
                      ))}
                    </div>
                    <span className="review-count">{displayDoctor.reviews || '100'} reviews</span>
                  </div>
                </div>
                
                {/* Sample Reviews */}
                <div className="reviews-list">
                  {[
                    { name: 'Rahul M.', rating: 5, date: '2 days ago', comment: 'Excellent doctor! Very thorough and explained everything clearly.' },
                    { name: 'Priyanka S.', rating: 5, date: '1 week ago', comment: 'Very professional and caring. Highly recommend!' },
                    { name: 'Amit K.', rating: 4, date: '2 weeks ago', comment: 'Good consultation but had to wait a bit.' }
                  ].map((review, idx) => (
                    <div key={idx} className="review-card">
                      <div className="review-header">
                        <div className="reviewer-avatar">{review.name.charAt(0)}</div>
                        <div className="reviewer-info">
                          <span className="reviewer-name">{review.name}</span>
                          <span className="review-date">{review.date}</span>
                        </div>
                        <div className="review-rating">
                          {[1, 2, 3, 4, 5].map(star => (
                            <FiStar key={star} className={star <= review.rating ? 'filled' : ''} />
                          ))}
                        </div>
                      </div>
                      <p className="review-comment">{review.comment}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'education' && (
              <div className="education-tab">
                <div className="info-section">
                  <h3>Education & Qualifications</h3>
                  <div className="education-list">
                    {(displayDoctor.education || [
                      { degree: 'MBBS', institution: 'Medical College', year: '2010' },
                      { degree: 'MD', institution: 'Medical University', year: '2014' }
                    ]).map((edu, idx) => (
                      <div key={idx} className="education-item">
                        <div className="edu-icon">🎓</div>
                        <div className="edu-info">
                          <span className="edu-degree">{edu.degree}</span>
                          <span className="edu-institution">{edu.institution}</span>
                          <span className="edu-year">{edu.year}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="info-section">
                  <h3>Awards & Recognition</h3>
                  <div className="awards-list">
                    {(displayDoctor.awards || ['Healthcare Excellence Award 2023']).map((award, idx) => (
                      <div key={idx} className="award-item">
                        <FiAward className="award-icon" />
                        <span>{award}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Booking Sidebar */}
        <div className="booking-sidebar">
          <div className="booking-card">
            <h3>Book Appointment</h3>
            
            {/* Date Selection */}
            <div className="date-selection">
              <h4><FiCalendar /> Select Date</h4>
              <div className="date-pills">
                {availableDates.map((dateObj) => (
                  <button
                    key={dateObj.full}
                    className={`date-pill ${selectedDate === dateObj.full ? 'active' : ''}`}
                    onClick={() => setSelectedDate(dateObj.full)}
                  >
                    <span className="day-name">{dateObj.day}</span>
                    <span className="day-num">{dateObj.dateNum}</span>
                    <span className="month-name">{dateObj.month}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Time Slots */}
            <div className="time-selection">
              <h4><FiClock /> Select Time</h4>
              
              {slotsLoading ? (
                <div className="slots-loading">Loading available slots...</div>
              ) : availableSlots.length === 0 ? (
                <div className="no-slots-message">
                  <p>No available time slots for this doctor.</p>
                  <p className="hint">The doctor needs to add availability first.</p>
                </div>
              ) : (
                <>
                  {timeSlots.morning && timeSlots.morning.length > 0 && (
                    <div className="slot-group">
                      <span className="slot-label">🌅 Morning</span>
                      <div className="time-slots">
                        {timeSlots.morning.map((slot) => (
                          <button
                            key={slot.id || slot}
                            className={`time-slot ${(selectedSlot?.id || selectedSlot) === (slot.id || slot) ? 'active' : ''}`}
                            onClick={() => setSelectedSlot(slot)}
                          >
                            {slot.displayTime || slot}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {timeSlots.afternoon && timeSlots.afternoon.length > 0 && (
                    <div className="slot-group">
                      <span className="slot-label">☀️ Afternoon</span>
                      <div className="time-slots">
                        {timeSlots.afternoon.map((slot) => (
                          <button
                            key={slot.id || slot}
                            className={`time-slot ${(selectedSlot?.id || selectedSlot) === (slot.id || slot) ? 'active' : ''}`}
                            onClick={() => setSelectedSlot(slot)}
                          >
                            {slot.displayTime || slot}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {timeSlots.evening && timeSlots.evening.length > 0 && (
                    <div className="slot-group">
                      <span className="slot-label">🌙 Evening</span>
                      <div className="time-slots">
                        {timeSlots.evening.map((slot) => (
                          <button
                            key={slot.id || slot}
                            className={`time-slot ${(selectedSlot?.id || selectedSlot) === (slot.id || slot) ? 'active' : ''}`}
                            onClick={() => setSelectedSlot(slot)}
                          >
                            {slot.displayTime || slot}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Consultation Type */}
            <div className="consultation-type">
              <h4>Consultation Type</h4>
              <div className="type-options">
                <button className="type-btn active">
                  <FiUser /> In-Clinic
                </button>
                <button className="type-btn">
                  <FiVideo /> Video Call
                </button>
              </div>
            </div>

            {/* Booking Summary */}
            <div className="booking-summary">
              <div className="summary-row">
                <span>Consultation Fee</span>
                <span>₹{displayDoctor.consultation_fee || '500'}</span>
              </div>
              <div className="summary-row">
                <span>Platform Fee</span>
                <span>₹50</span>
              </div>
              <div className="summary-row total">
                <span>Total</span>
                <span>₹{(displayDoctor.consultation_fee || 500) + 50}</span>
              </div>
            </div>

            {/* Book Button */}
            <button 
              className="book-appointment-btn"
              onClick={handleBookAppointment}
              disabled={bookingLoading || !selectedDate || !selectedSlot}
            >
              {bookingLoading ? (
                <>
                  <span className="spinner small"></span>
                  Booking...
                </>
              ) : (
                <>
                  Book Appointment <FiChevronRight />
                </>
              )}
            </button>

            {!isAuthenticated && (
              <p className="login-note">
                Please <Link to="/login">login</Link> to book an appointment
              </p>
            )}
          </div>

          {/* Contact Card */}
          <div className="contact-card">
            <h4>Need Help?</h4>
            <p>Contact our support team</p>
            <a href="tel:+911234567890" className="contact-link">
              <FiPhone /> +91 12345 67890
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DoctorProfile;
