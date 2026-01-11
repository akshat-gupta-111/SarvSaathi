import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check for existing auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user');
      
      if (accessToken && savedUser) {
        try {
          // Verify token is still valid by making a health check
          await authAPI.healthCheck();
          setUser(JSON.parse(savedUser));
          setIsAuthenticated(true);
        } catch (error) {
          // Token is invalid, try to refresh
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const response = await authAPI.refreshToken(refreshToken);
              localStorage.setItem('access_token', response.data.access);
              setUser(JSON.parse(savedUser));
              setIsAuthenticated(true);
            } catch (refreshError) {
              // Refresh failed, clear everything
              logout();
            }
          } else {
            logout();
          }
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  // Login function
  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password);
      const { access, refresh } = response.data;
      
      // Store tokens
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      
      // Decode JWT to get user info (basic decode)
      const payload = JSON.parse(atob(access.split('.')[1]));
      const userData = {
        id: payload.user_id,
        email: email,
        user_type: payload.user_type || 'patient',
      };
      
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      setIsAuthenticated(true);
      
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message ||
                          'Login failed. Please check your credentials.';
      return { success: false, error: errorMessage };
    }
  };

  // Register function
  const register = async (email, password, userType, otpCode) => {
    try {
      await authAPI.registerWithOTP({
        email,
        password,
        user_type: userType,
        otp_code: otpCode,
      });
      
      // Auto-login after registration
      return await login(email, password);
    } catch (error) {
      const errorMessage = error.response?.data?.email?.[0] ||
                          error.response?.data?.otp_code?.[0] ||
                          error.response?.data?.detail ||
                          'Registration failed. Please try again.';
      return { success: false, error: errorMessage };
    }
  };

  // Send OTP function
  const sendOTP = async (email, phone_number, otp_type = 'email') => {
    try {
      const data = { otp_type };
      if (email) data.email = email;
      if (phone_number) data.phone_number = phone_number;
      
      const response = await authAPI.sendOTP(data);
      return { 
        success: true, 
        message: response.data.message,
        // For development only - remove in production
        otp_code: response.data.otp_code,
      };
    } catch (error) {
      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.error ||
                          'Failed to send OTP. Please try again.';
      return { success: false, error: errorMessage };
    }
  };

  // Verify OTP function
  const verifyOTP = async (email, phone_number, otp_code, otp_type = 'email') => {
    try {
      const data = { otp_code, otp_type };
      if (email) data.email = email;
      if (phone_number) data.phone_number = phone_number;
      
      const response = await authAPI.verifyOTP(data);
      return { success: response.data.verified, message: response.data.message };
    } catch (error) {
      const errorMessage = error.response?.data?.message ||
                          error.response?.data?.detail ||
                          'OTP verification failed.';
      return { success: false, error: errorMessage };
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    register,
    sendOTP,
    verifyOTP,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
