import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from '../../context/AuthContext';
import { FiMail, FiLock, FiEye, FiEyeOff } from 'react-icons/fi';
import './Auth.css';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user types
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
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    
    const result = await login(formData.email, formData.password);
    
    if (result.success) {
      toast.success('Login successful! Welcome back.');
      navigate('/');
    } else {
      toast.error(result.error);
      setErrors({ general: result.error });
    }
    
    setLoading(false);
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* Logo Section */}
        <div className="auth-header">
          <div className="auth-logo">
            <span className="logo-icon">🏥</span>
            <span className="logo-text">SarvSaathi</span>
          </div>
          <h1>Welcome Back</h1>
          <p>Sign in to continue to your healthcare dashboard</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {errors.general && (
            <div className="error-banner">{errors.general}</div>
          )}
          
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
                placeholder="Enter your password"
                className={errors.password ? 'input-error' : ''}
                autoComplete="current-password"
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
          </div>

          {/* Forgot Password Link */}
          <div className="auth-options">
            <Link to="/forgot-password" className="forgot-link">
              Forgot password?
            </Link>
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
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Register Link */}
        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/register" className="auth-link">
              Create account
            </Link>
          </p>
        </div>
      </div>

      {/* Side Decoration */}
      <div className="auth-decoration">
        <div className="decoration-content">
          <h2>Your Health, Our Priority</h2>
          <p>
            Access world-class healthcare services, book appointments with top 
            specialists, and manage your family's health all in one place.
          </p>
          <div className="decoration-features">
            <div className="feature">
              <span className="feature-icon">🏥</span>
              <span>Find Nearby Hospitals</span>
            </div>
            <div className="feature">
              <span className="feature-icon">👨‍⚕️</span>
              <span>Expert Doctors</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🚑</span>
              <span>Emergency Services</span>
            </div>
            <div className="feature">
              <span className="feature-icon">📱</span>
              <span>Online Consultations</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
