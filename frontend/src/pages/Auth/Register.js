import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from '../../context/AuthContext';
import { FiMail, FiLock, FiEye, FiEyeOff, FiPhone } from 'react-icons/fi';
import './Auth.css';

const Register = () => {
  const navigate = useNavigate();
  const { sendOTP } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    userType: 'patient',
    verificationMethod: 'email', // 'email' or 'phone'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }
    
    if (formData.verificationMethod === 'phone' && !formData.phone) {
      newErrors.phone = 'Phone number is required for phone verification';
    } else if (formData.phone && !/^\+?[1-9]\d{9,14}$/.test(formData.phone.replace(/\s/g, ''))) {
      newErrors.phone = 'Please enter a valid phone number (e.g., +919876543210)';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and a number';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    
    // Send OTP based on verification method
    const otpData = formData.verificationMethod === 'email' 
      ? { email: formData.email }
      : { phone_number: formData.phone };
    
    const result = await sendOTP(
      otpData.email,
      otpData.phone_number,
      formData.verificationMethod
    );
    
    if (result.success) {
      toast.success('OTP sent! Please check your ' + 
        (formData.verificationMethod === 'email' ? 'email inbox' : 'phone'));
      
      // Navigate to OTP verification page with form data
      navigate('/verify-otp', { 
        state: { 
          email: formData.email,
          phone: formData.phone,
          password: formData.password,
          userType: formData.userType,
          verificationMethod: formData.verificationMethod,
          // For development only - remove in production
          debugOTP: result.otp_code,
        } 
      });
    } else {
      toast.error(result.error);
      setErrors({ general: result.error });
    }
    
    setLoading(false);
  };

  return (
    <div className="auth-container">
      <div className="auth-card register-card">
        {/* Logo Section */}
        <div className="auth-header">
          <div className="auth-logo">
            <span className="logo-icon">🏥</span>
            <span className="logo-text">SarvSaathi</span>
          </div>
          <h1>Create Account</h1>
          <p>Join SarvSaathi for better healthcare management</p>
        </div>

        {/* Register Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {errors.general && (
            <div className="error-banner">{errors.general}</div>
          )}

          {/* User Type Selection */}
          <div className="input-group">
            <label>I am a</label>
            <div className="user-type-selector">
              <button
                type="button"
                className={`type-btn ${formData.userType === 'patient' ? 'active' : ''}`}
                onClick={() => handleChange({ target: { name: 'userType', value: 'patient' } })}
              >
                <span className="type-icon">👤</span>
                Patient
              </button>
              <button
                type="button"
                className={`type-btn ${formData.userType === 'doctor' ? 'active' : ''}`}
                onClick={() => handleChange({ target: { name: 'userType', value: 'doctor' } })}
              >
                <span className="type-icon">👨‍⚕️</span>
                Doctor
              </button>
            </div>
          </div>

          {/* Email Input */}
          <div className="input-group">
            <label htmlFor="email">Email Address</label>
            <div className="input-wrapper">
              <FiMail className="input-icon" />
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                className={errors.email ? 'input-error' : ''}
                autoComplete="email"
              />
            </div>
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>

          {/* Phone Input */}
          <div className="input-group">
            <label htmlFor="phone">Phone Number (Optional)</label>
            <div className="input-wrapper">
              <FiPhone className="input-icon" />
              <input
                type="tel"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+91 9876543210"
                className={errors.phone ? 'input-error' : ''}
                autoComplete="tel"
              />
            </div>
            {errors.phone && <span className="error-message">{errors.phone}</span>}
          </div>

          {/* Verification Method */}
          <div className="input-group">
            <label>Verify via</label>
            <div className="verification-selector">
              <label className="radio-option">
                <input
                  type="radio"
                  name="verificationMethod"
                  value="email"
                  checked={formData.verificationMethod === 'email'}
                  onChange={handleChange}
                />
                <span className="radio-label">📧 Email OTP</span>
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  name="verificationMethod"
                  value="phone"
                  checked={formData.verificationMethod === 'phone'}
                  onChange={handleChange}
                  disabled={!formData.phone}
                />
                <span className="radio-label">📱 Phone OTP</span>
              </label>
            </div>
          </div>

          {/* Password Input */}
          <div className="input-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <FiLock className="input-icon" />
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Create a strong password"
                className={errors.password ? 'input-error' : ''}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
            {errors.password && <span className="error-message">{errors.password}</span>}
            <div className="password-hints">
              <span className={formData.password.length >= 8 ? 'hint-valid' : ''}>
                8+ characters
              </span>
              <span className={/[A-Z]/.test(formData.password) ? 'hint-valid' : ''}>
                Uppercase
              </span>
              <span className={/[a-z]/.test(formData.password) ? 'hint-valid' : ''}>
                Lowercase
              </span>
              <span className={/\d/.test(formData.password) ? 'hint-valid' : ''}>
                Number
              </span>
            </div>
          </div>

          {/* Confirm Password */}
          <div className="input-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <div className="input-wrapper">
              <FiLock className="input-icon" />
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Confirm your password"
                className={errors.confirmPassword ? 'input-error' : ''}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
            {errors.confirmPassword && <span className="error-message">{errors.confirmPassword}</span>}
          </div>

          {/* Terms & Conditions */}
          <div className="terms-text">
            By creating an account, you agree to our{' '}
            <Link to="/terms">Terms of Service</Link> and{' '}
            <Link to="/privacy">Privacy Policy</Link>
          </div>

          {/* Submit Button */}
          <button 
            type="submit" 
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Sending OTP...
              </>
            ) : (
              'Continue with OTP'
            )}
          </button>
        </form>

        {/* Login Link */}
        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Sign in
            </Link>
          </p>
        </div>
      </div>

      {/* Side Decoration */}
      <div className="auth-decoration">
        <div className="decoration-content">
          <h2>Join Our Healthcare Family</h2>
          <p>
            Get started with SarvSaathi and experience healthcare like never before.
            Book appointments, manage family health, and access emergency services.
          </p>
          <div className="decoration-features">
            <div className="feature">
              <span className="feature-icon">✅</span>
              <span>Verified Doctors</span>
            </div>
            <div className="feature">
              <span className="feature-icon">👨‍👩‍👧‍👦</span>
              <span>Family Accounts</span>
            </div>
            <div className="feature">
              <span className="feature-icon">💳</span>
              <span>Secure Payments</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🔒</span>
              <span>Data Privacy</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
