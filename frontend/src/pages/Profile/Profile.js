import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { patientAPI, doctorAPI, appointmentsAPI } from '../../api';
import { toast } from 'react-toastify';
import {
  FiUser, FiMapPin, FiCalendar, FiEdit2,
  FiCamera, FiShield, FiSettings, FiHeart, FiClock, FiFileText,
  FiLock, FiBell, FiLogOut, FiChevronRight, FiCheck, FiX,
  FiSave, FiBriefcase
} from 'react-icons/fi';
import './Profile.css';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('profile');
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Profile data
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    gender: '',
    blood_group: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    emergency_contact: '',
    // Doctor specific fields
    specialty: '',
    qualification: '',
    experience: '',
    consultation_fee: '',
    clinic_name: '',
    clinic_address: '',
    bio: ''
  });

  // Appointments data
  const [appointments, setAppointments] = useState([]);

  useEffect(() => {
    fetchProfile();
    fetchAppointments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAppointments = async () => {
    try {
      if (user?.user_type === 'doctor') {
        const response = await appointmentsAPI.getDoctorAppointments();
        setAppointments(response.data || []);
      } else {
        const response = await appointmentsAPI.getMyAppointments();
        setAppointments(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching appointments:', error);
      setAppointments([]);
    }
  };

  const fetchProfile = async () => {
    setLoading(true);
    try {
      if (user?.user_type === 'doctor') {
        const response = await doctorAPI.getMyProfile();
        setProfileData(prev => ({ ...prev, ...response.data }));
      } else {
        const response = await patientAPI.getProfile();
        // Map backend response to form fields
        const data = response.data;
        setProfileData(prev => ({
          ...prev,
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          email: data.email || '',
          phone: data.phone_number || '',
          date_of_birth: data.date_of_birth || '',
          // Profile nested fields
          gender: data.profile?.gender || '',
          blood_group: data.profile?.blood_group || '',
          address: data.profile?.address_line1 || '',
          city: data.profile?.city || '',
          state: data.profile?.state || '',
          pincode: data.profile?.pincode || '',
        }));
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      // Use user data as fallback
      setProfileData(prev => ({
        ...prev,
        email: user?.email || '',
        first_name: user?.first_name || '',
        last_name: user?.last_name || ''
      }));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      // Format data for backend - separate user fields from profile fields
      const updateData = {
        first_name: profileData.first_name,
        last_name: profileData.last_name,
        phone_number: profileData.phone || profileData.phone_number,
        date_of_birth: profileData.date_of_birth || null,
        profile: {
          gender: profileData.gender,
          blood_group: profileData.blood_group,
          address_line1: profileData.address || profileData.address_line1,
          city: profileData.city,
          state: profileData.state,
          pincode: profileData.pincode,
        }
      };

      if (user?.user_type === 'doctor') {
        // Doctor profile has different structure
        const doctorData = {
          specialty: profileData.specialty,
          qualification: profileData.qualification,
          years_of_experience: profileData.experience,
          consultation_fee: profileData.consultation_fee,
          clinic_name: profileData.clinic_name,
          clinic_address: profileData.clinic_address,
          bio: profileData.bio
        };
        await doctorAPI.updateProfile(doctorData);
      } else {
        await patientAPI.updateProfile(updateData);
      }
      toast.success('Profile updated successfully!');
      setIsEditing(false);
      // Refresh profile data
      fetchProfile();
    } catch (error) {
      console.error('Error saving profile:', error);
      const errorMsg = error.response?.data?.detail || 
                      error.response?.data?.error ||
                      'Failed to update profile';
      toast.error(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const menuItems = [
    { id: 'profile', icon: FiUser, label: 'My Profile' },
    { id: 'appointments', icon: FiCalendar, label: 'Appointments' },
    { id: 'medical', icon: FiFileText, label: 'Medical Records' },
    { id: 'favorites', icon: FiHeart, label: 'Favorites' },
    { id: 'settings', icon: FiSettings, label: 'Settings' },
  ];

  if (loading) {
    return (
      <div className="profile-loading">
        <div className="loading-spinner"></div>
        <p>Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="profile-page">
      {/* Sidebar */}
      <aside className="profile-sidebar">
        {/* User Card */}
        <div className="user-card">
          <div className="user-avatar-container">
            <div className="user-avatar">
              {profileData.first_name?.charAt(0) || user?.email?.charAt(0).toUpperCase()}
            </div>
            <button className="avatar-edit-btn">
              <FiCamera />
            </button>
          </div>
          <h3>{profileData.first_name} {profileData.last_name || user?.email?.split('@')[0]}</h3>
          <p className="user-email">{user?.email}</p>
          <span className={`user-type-badge ${user?.user_type}`}>
            {user?.user_type === 'doctor' ? '👨‍⚕️ Doctor' : '🏥 Patient'}
          </span>
          {user?.user_type === 'doctor' && profileData.is_verified && (
            <span className="verified-badge">
              <FiShield /> Verified
            </span>
          )}
        </div>

        {/* Navigation Menu */}
        <nav className="profile-nav">
          {menuItems.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <item.icon />
              <span>{item.label}</span>
              <FiChevronRight className="nav-arrow" />
            </button>
          ))}
        </nav>

        {/* Logout Button */}
        <button className="logout-btn" onClick={handleLogout}>
          <FiLogOut />
          <span>Logout</span>
        </button>
      </aside>

      {/* Main Content */}
      <main className="profile-main">
        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="profile-content">
            <div className="content-header">
              <h2>My Profile</h2>
              {!isEditing ? (
                <button className="edit-btn" onClick={() => setIsEditing(true)}>
                  <FiEdit2 /> Edit Profile
                </button>
              ) : (
                <div className="edit-actions">
                  <button className="cancel-btn" onClick={() => setIsEditing(false)}>
                    <FiX /> Cancel
                  </button>
                  <button className="save-btn" onClick={handleSaveProfile} disabled={saving}>
                    {saving ? <span className="spinner small"></span> : <FiSave />}
                    Save Changes
                  </button>
                </div>
              )}
            </div>

            {/* Personal Information */}
            <section className="profile-section">
              <h3><FiUser /> Personal Information</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label>First Name</label>
                  <input
                    type="text"
                    name="first_name"
                    value={profileData.first_name}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="Enter first name"
                  />
                </div>
                <div className="form-group">
                  <label>Last Name</label>
                  <input
                    type="text"
                    name="last_name"
                    value={profileData.last_name}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="Enter last name"
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    name="email"
                    value={profileData.email || user?.email}
                    disabled
                    className="disabled"
                  />
                </div>
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    name="phone"
                    value={profileData.phone}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="Enter phone number"
                  />
                </div>
                <div className="form-group">
                  <label>Date of Birth</label>
                  <input
                    type="date"
                    name="date_of_birth"
                    value={profileData.date_of_birth}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                  />
                </div>
                <div className="form-group">
                  <label>Gender</label>
                  <select
                    name="gender"
                    value={profileData.gender}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                  >
                    <option value="">Select Gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
            </section>

            {/* Medical Information (Patient only) */}
            {user?.user_type === 'patient' && (
              <section className="profile-section">
                <h3><FiHeart /> Medical Information</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Blood Group</label>
                    <select
                      name="blood_group"
                      value={profileData.blood_group}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                    >
                      <option value="">Select Blood Group</option>
                      <option value="A+">A+</option>
                      <option value="A-">A-</option>
                      <option value="B+">B+</option>
                      <option value="B-">B-</option>
                      <option value="AB+">AB+</option>
                      <option value="AB-">AB-</option>
                      <option value="O+">O+</option>
                      <option value="O-">O-</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Emergency Contact</label>
                    <input
                      type="tel"
                      name="emergency_contact"
                      value={profileData.emergency_contact}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="Emergency contact number"
                    />
                  </div>
                </div>
              </section>
            )}

            {/* Professional Information (Doctor only) */}
            {user?.user_type === 'doctor' && (
              <section className="profile-section">
                <h3><FiBriefcase /> Professional Information</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Specialty</label>
                    <select
                      name="specialty"
                      value={profileData.specialty}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                    >
                      <option value="">Select Specialty</option>
                      <option value="Cardiology">Cardiology</option>
                      <option value="Dermatology">Dermatology</option>
                      <option value="Pediatrics">Pediatrics</option>
                      <option value="Orthopedics">Orthopedics</option>
                      <option value="Neurology">Neurology</option>
                      <option value="Gynecology">Gynecology</option>
                      <option value="Psychiatry">Psychiatry</option>
                      <option value="General Physician">General Physician</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Qualification</label>
                    <input
                      type="text"
                      name="qualification"
                      value={profileData.qualification}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="e.g., MBBS, MD"
                    />
                  </div>
                  <div className="form-group">
                    <label>Experience (years)</label>
                    <input
                      type="number"
                      name="experience"
                      value={profileData.experience}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="Years of experience"
                    />
                  </div>
                  <div className="form-group">
                    <label>Consultation Fee (₹)</label>
                    <input
                      type="number"
                      name="consultation_fee"
                      value={profileData.consultation_fee}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="Fee amount"
                    />
                  </div>
                  <div className="form-group full-width">
                    <label>Clinic Name</label>
                    <input
                      type="text"
                      name="clinic_name"
                      value={profileData.clinic_name}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="Name of your clinic"
                    />
                  </div>
                  <div className="form-group full-width">
                    <label>Clinic Address</label>
                    <textarea
                      name="clinic_address"
                      value={profileData.clinic_address}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="Full clinic address"
                      rows={3}
                    />
                  </div>
                  <div className="form-group full-width">
                    <label>Bio</label>
                    <textarea
                      name="bio"
                      value={profileData.bio}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      placeholder="Tell patients about yourself..."
                      rows={4}
                    />
                  </div>
                </div>
              </section>
            )}

            {/* Address Information */}
            <section className="profile-section">
              <h3><FiMapPin /> Address Information</h3>
              <div className="form-grid">
                <div className="form-group full-width">
                  <label>Address</label>
                  <input
                    type="text"
                    name="address"
                    value={profileData.address}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="Street address"
                  />
                </div>
                <div className="form-group">
                  <label>City</label>
                  <input
                    type="text"
                    name="city"
                    value={profileData.city}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="City"
                  />
                </div>
                <div className="form-group">
                  <label>State</label>
                  <input
                    type="text"
                    name="state"
                    value={profileData.state}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="State"
                  />
                </div>
                <div className="form-group">
                  <label>PIN Code</label>
                  <input
                    type="text"
                    name="pincode"
                    value={profileData.pincode}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    placeholder="PIN code"
                  />
                </div>
              </div>
            </section>
          </div>
        )}

        {/* Appointments Tab */}
        {activeTab === 'appointments' && (
          <div className="appointments-content">
            <div className="content-header">
              <h2>My Appointments</h2>
              <Link to="/search" className="book-new-btn">
                + Book New Appointment
              </Link>
            </div>

            {/* Appointment Tabs */}
            <div className="appointment-tabs">
              <button className="apt-tab active">All</button>
              <button className="apt-tab">Upcoming</button>
              <button className="apt-tab">Completed</button>
              <button className="apt-tab">Cancelled</button>
            </div>

            {/* Appointments List */}
            <div className="appointments-list">
              {appointments.length === 0 ? (
                <div className="no-appointments">
                  <FiCalendar size={48} />
                  <h3>No Appointments</h3>
                  <p>You don't have any appointments yet.</p>
                  <Link to="/search-doctors" className="book-now-btn">Find a Doctor</Link>
                </div>
              ) : (
                appointments.map(apt => (
                  <div key={apt.id} className={`appointment-card ${apt.status}`}>
                    <div className="apt-left">
                      <div className="apt-avatar">
                        {apt.doctor_name?.split(' ')[1]?.charAt(0) || apt.time_slot?.doctor?.user?.first_name?.charAt(0) || 'D'}
                      </div>
                    </div>
                    <div className="apt-middle">
                      <h4>{apt.doctor_name || `Dr. ${apt.time_slot?.doctor?.user?.first_name || ''} ${apt.time_slot?.doctor?.user?.last_name || ''}`}</h4>
                      <p className="apt-specialty">{apt.specialty || apt.time_slot?.doctor?.specialty || 'Specialist'}</p>
                      <div className="apt-details">
                        <span><FiCalendar /> {apt.date || apt.time_slot?.date}</span>
                        <span><FiClock /> {apt.time || apt.time_slot?.start_time}</span>
                        <span className="apt-type">{apt.type || 'In-Clinic'}</span>
                      </div>
                    </div>
                    <div className="apt-right">
                      <span className={`apt-status ${apt.status}`}>
                        {apt.status === 'upcoming' && <FiClock />}
                        {apt.status === 'confirmed' && <FiClock />}
                        {apt.status === 'completed' && <FiCheck />}
                        {apt.status}
                      </span>
                      {(apt.status === 'upcoming' || apt.status === 'confirmed') && (
                        <div className="apt-actions">
                          <button className="reschedule-btn">Reschedule</button>
                          <button className="cancel-apt-btn">Cancel</button>
                        </div>
                      )}
                      {apt.status === 'completed' && (
                        <button className="review-btn">Write Review</button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Medical Records Tab */}
        {activeTab === 'medical' && (
          <div className="medical-content">
            <div className="content-header">
              <h2>Medical Records</h2>
              <button className="upload-btn">
                + Upload Record
              </button>
            </div>

            <div className="empty-state">
              <FiFileText className="empty-icon" />
              <h3>No Medical Records</h3>
              <p>Upload your medical records, prescriptions, and reports here for easy access.</p>
              <button className="btn-primary">Upload Your First Record</button>
            </div>
          </div>
        )}

        {/* Favorites Tab */}
        {activeTab === 'favorites' && (
          <div className="favorites-content">
            <div className="content-header">
              <h2>Favorite Doctors</h2>
            </div>

            <div className="empty-state">
              <FiHeart className="empty-icon" />
              <h3>No Favorites Yet</h3>
              <p>Save your favorite doctors for quick access when booking appointments.</p>
              <Link to="/search" className="btn-primary">Find Doctors</Link>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="settings-content">
            <div className="content-header">
              <h2>Settings</h2>
            </div>

            <div className="settings-list">
              {/* Notifications */}
              <div className="setting-item">
                <div className="setting-info">
                  <FiBell className="setting-icon" />
                  <div>
                    <h4>Notifications</h4>
                    <p>Manage your notification preferences</p>
                  </div>
                </div>
                <FiChevronRight />
              </div>

              {/* Privacy */}
              <div className="setting-item">
                <div className="setting-info">
                  <FiLock className="setting-icon" />
                  <div>
                    <h4>Privacy & Security</h4>
                    <p>Manage your account security</p>
                  </div>
                </div>
                <FiChevronRight />
              </div>

              {/* Change Password */}
              <div className="setting-item">
                <div className="setting-info">
                  <FiShield className="setting-icon" />
                  <div>
                    <h4>Change Password</h4>
                    <p>Update your password</p>
                  </div>
                </div>
                <FiChevronRight />
              </div>

              {/* Language */}
              <div className="setting-item">
                <div className="setting-info">
                  <span className="setting-icon">🌐</span>
                  <div>
                    <h4>Language</h4>
                    <p>English</p>
                  </div>
                </div>
                <FiChevronRight />
              </div>

              {/* Help */}
              <div className="setting-item">
                <div className="setting-info">
                  <span className="setting-icon">❓</span>
                  <div>
                    <h4>Help & Support</h4>
                    <p>Get help or contact us</p>
                  </div>
                </div>
                <FiChevronRight />
              </div>

              {/* About */}
              <div className="setting-item">
                <div className="setting-info">
                  <span className="setting-icon">ℹ️</span>
                  <div>
                    <h4>About SarvSaathi</h4>
                    <p>Version 1.0.0</p>
                  </div>
                </div>
                <FiChevronRight />
              </div>
            </div>

            {/* Danger Zone */}
            <div className="danger-zone">
              <h3>Danger Zone</h3>
              <button className="delete-account-btn">
                Delete Account
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Profile;
