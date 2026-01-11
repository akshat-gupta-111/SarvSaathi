import axios from 'axios';

// Base URL for the Django backend API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          
          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  // Send OTP to email or phone
  sendOTP: (data) => api.post('/accounts/send-otp/', data),
  
  // Verify OTP
  verifyOTP: (data) => api.post('/accounts/verify-otp/', data),
  
  // Register with OTP verification
  registerWithOTP: (data) => api.post('/accounts/register-with-otp/', data),
  
  // Register without OTP (legacy)
  register: (data) => api.post('/accounts/register/', data),
  
  // Login (get JWT tokens)
  login: (email, password) => api.post('/token/', { email, password }),
  
  // Refresh token
  refreshToken: (refresh) => api.post('/token/refresh/', { refresh }),
  
  // Health check
  healthCheck: () => api.get('/accounts/health-check/'),
};

// Patient API calls
export const patientAPI = {
  // Get logged-in user's profile (user + extended profile)
  getProfile: () => api.get('/accounts/me/'),
  
  // Update logged-in user's profile
  updateProfile: (data) => api.patch('/accounts/me/', data),
  
  // Get all family members/patient profiles for logged-in user
  getPatients: () => api.get('/accounts/patients/'),
  getFamilyMembers: () => api.get('/accounts/family-members/'),
  
  // Create a new family member/patient profile
  createPatient: (data) => api.post('/accounts/patients/', data),
  createFamilyMember: (data) => api.post('/accounts/family-members/', data),
  
  // Get a specific family member/patient profile
  getPatient: (id) => api.get(`/accounts/patients/${id}/`),
  
  // Update a family member/patient profile
  updatePatient: (id, data) => api.put(`/accounts/patients/${id}/`, data),
  
  // Delete a family member/patient profile
  deletePatient: (id) => api.delete(`/accounts/patients/${id}/`),
};

// Doctor API calls
export const doctorAPI = {
  // Get logged-in doctor's full profile (doctor-specific)
  getProfile: () => api.get('/accounts/doctor-profile/'),
  getMyProfile: () => api.get('/accounts/doctor-profile/'),
  
  // Update doctor's profile
  updateProfile: (data) => api.patch('/accounts/doctor-profile/', data),
  
  // Get all verified doctors (public)
  getVerifiedDoctors: (params = {}) => api.get('/accounts/doctors/verified/', { params }),
  
  // Get single doctor details
  getDoctorDetail: (id) => api.get(`/accounts/doctors/${id}/`),
  getDoctorProfile: (id) => api.get(`/accounts/doctors/${id}/`),  // Alias for backward compatibility
  
  // Search doctors with filters
  searchDoctors: (filters) => {
    const params = new URLSearchParams();
    if (filters.specialty) params.append('specialty', filters.specialty);
    if (filters.min_fee) params.append('min_fee', filters.min_fee);
    if (filters.max_fee) params.append('max_fee', filters.max_fee);
    if (filters.min_experience) params.append('min_experience', filters.min_experience);
    if (filters.sort) params.append('sort', filters.sort);
    return api.get(`/accounts/doctors/?${params.toString()}`);
  },
};

// Appointments API calls
export const appointmentsAPI = {
  // Doctor: Create time slot
  createTimeSlot: (data) => api.post('/appointments/time-slots/', data),
  
  // Doctor: Get own time slots
  getTimeSlots: () => api.get('/appointments/time-slots/'),
  
  // Patient: Get available slots for a doctor
  getDoctorSlots: (doctorId) => api.get(`/appointments/doctors/${doctorId}/time-slots/`),
  
  // Patient: Book an appointment
  bookAppointment: (data) => api.post('/appointments/book/', data),
  createAppointment: (data) => api.post('/appointments/book/', data),  // Alias for backward compatibility
  
  // Execute payment after PayPal approval
  executePayment: (data) => api.post('/appointments/execute-payment/', data),
  
  // Patient: Get own appointments
  getMyAppointments: () => api.get('/appointments/my-appointments/'),
  
  // Doctor: Get own appointments (schedule)
  getMySchedule: () => api.get('/appointments/doctor/appointments/'),
  getDoctorAppointments: () => api.get('/appointments/doctor/appointments/'),
};

// Emergency API calls
export const emergencyAPI = {
  // Find nearby specialists
  findSpecialist: (data) => api.post('/emergency/find-specialist/', data),
  
  // Request a specific doctor
  requestDoctor: (data) => api.post('/emergency/request-doctor/', data),
  
  // Trigger emergency SOS alert
  triggerEmergency: (data) => api.post('/emergency/trigger-sos/', data),
  
  // Get emergency contacts (from accounts app - new architecture)
  getEmergencyContacts: () => api.get('/accounts/emergency-contacts/'),
  
  // Add emergency contact
  addEmergencyContact: (data) => api.post('/accounts/emergency-contacts/', data),
  
  // Update emergency contact
  updateEmergencyContact: (id, data) => api.patch(`/accounts/emergency-contacts/${id}/`, data),
  
  // Delete emergency contact
  deleteEmergencyContact: (id) => api.delete(`/accounts/emergency-contacts/${id}/`),
  
  // Get nearby hospitals (mock - needs external API integration)
  getNearbyHospitals: (lat, lng) => api.get(`/emergency/hospitals/?lat=${lat}&lng=${lng}`),
};

// ML Service API calls (different base URL)
const ML_API_URL = process.env.REACT_APP_ML_URL || 'http://127.0.0.1:5001';

export const mlAPI = {
  // Health check
  healthCheck: () => axios.get(`${ML_API_URL}/health`),
  
  // Get symptom guidance
  getGuidance: (data) => axios.post(`${ML_API_URL}/generate_guidance`, data),
  
  // No-show prediction (internal use)
  predictNoShow: (data) => axios.post(`${ML_API_URL}/predict`, data),
};

export default api;
