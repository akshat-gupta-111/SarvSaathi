import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from '../../context/AuthContext';
import { FiArrowLeft, FiRefreshCw } from 'react-icons/fi';
import './Auth.css';

const VerifyOTP = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { register, sendOTP, verifyOTP } = useAuth();
  
  // Get data from registration
  const { email, phone, password, userType, verificationMethod, debugOTP } = location.state || {};
  
  // Redirect if no data
  useEffect(() => {
    if (!email) {
      navigate('/register');
    }
  }, [email, navigate]);

  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const inputRefs = useRef([]);

  // Countdown timer for resend
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [countdown]);

  // Handle OTP input change
  const handleChange = (index, value) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;
    
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    
    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  // Handle backspace
  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  // Handle paste
  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, 6);
    if (/^\d+$/.test(pastedData)) {
      const newOtp = pastedData.split('').concat(Array(6 - pastedData.length).fill(''));
      setOtp(newOtp);
      inputRefs.current[Math.min(pastedData.length, 5)]?.focus();
    }
  };

  // Resend OTP
  const handleResend = async () => {
    setResendLoading(true);
    
    const result = await sendOTP(
      verificationMethod === 'email' ? email : null,
      verificationMethod === 'phone' ? phone : null,
      verificationMethod
    );
    
    if (result.success) {
      toast.success('OTP resent successfully!');
      setCountdown(60);
      setCanResend(false);
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
      
      // For development - show debug OTP
      if (result.otp_code) {
        console.log('Debug OTP:', result.otp_code);
      }
    } else {
      toast.error(result.error);
    }
    
    setResendLoading(false);
  };

  // Verify and Register
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const otpCode = otp.join('');
    if (otpCode.length !== 6) {
      toast.error('Please enter the complete 6-digit OTP');
      return;
    }
    
    setLoading(true);
    
    // Register with OTP
    const result = await register(email, password, userType, otpCode);
    
    if (result.success) {
      toast.success('Account created successfully! Welcome to SarvSaathi.');
      navigate('/');
    } else {
      toast.error(result.error);
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    }
    
    setLoading(false);
  };

  const identifier = verificationMethod === 'email' ? email : phone;
  const identifierType = verificationMethod === 'email' ? 'email' : 'phone';

  return (
    <div className="auth-container">
      <div className="auth-card otp-card">
        {/* Back Button */}
        <Link to="/register" className="back-button">
          <FiArrowLeft /> Back
        </Link>

        {/* Header */}
        <div className="auth-header">
          <div className="otp-icon">📧</div>
          <h1>Verify Your {identifierType === 'email' ? 'Email' : 'Phone'}</h1>
          <p>
            We've sent a 6-digit verification code to<br />
            <strong>{identifier}</strong>
          </p>
        </div>

        {/* Debug OTP Display (Development Only) */}
        {debugOTP && (
          <div className="debug-otp">
            <span>🔧 Debug Mode: Your OTP is </span>
            <strong>{debugOTP}</strong>
          </div>
        )}

        {/* OTP Form */}
        <form onSubmit={handleSubmit} className="otp-form">
          <div className="otp-inputs">
            {otp.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={handlePaste}
                className="otp-input"
                autoFocus={index === 0}
              />
            ))}
          </div>

          {/* Resend Option */}
          <div className="resend-section">
            {canResend ? (
              <button
                type="button"
                className="resend-btn"
                onClick={handleResend}
                disabled={resendLoading}
              >
                {resendLoading ? (
                  <>
                    <span className="spinner small"></span>
                    Sending...
                  </>
                ) : (
                  <>
                    <FiRefreshCw /> Resend Code
                  </>
                )}
              </button>
            ) : (
              <p className="resend-timer">
                Resend code in <strong>{countdown}s</strong>
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button 
            type="submit" 
            className="btn btn-primary btn-block"
            disabled={loading || otp.join('').length !== 6}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Verifying...
              </>
            ) : (
              'Verify & Create Account'
            )}
          </button>
        </form>

        {/* Help Text */}
        <div className="otp-help">
          <p>
            Didn't receive the code? Check your spam folder or{' '}
            <button 
              type="button" 
              className="link-btn"
              onClick={() => navigate('/register')}
            >
              try a different {identifierType}
            </button>
          </p>
        </div>
      </div>

      {/* Side Decoration */}
      <div className="auth-decoration">
        <div className="decoration-content">
          <h2>Almost There!</h2>
          <p>
            Just one more step to complete your registration. 
            Enter the verification code to secure your account.
          </p>
          <div className="security-badges">
            <div className="badge">
              <span className="badge-icon">🔐</span>
              <div>
                <strong>Secure Verification</strong>
                <span>Your data is encrypted</span>
              </div>
            </div>
            <div className="badge">
              <span className="badge-icon">⏱️</span>
              <div>
                <strong>Quick Setup</strong>
                <span>Takes less than a minute</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyOTP;
