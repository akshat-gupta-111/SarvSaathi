import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Context
import { AuthProvider, useAuth } from './context/AuthContext';

// Components
import Navbar from './components/Navbar';
import Footer from './components/Footer';

// Pages
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import VerifyOTP from './pages/Auth/VerifyOTP';
import Home from './pages/Home';
import SearchDoctors from './pages/SearchDoctors';
import DoctorProfile from './pages/DoctorProfile';
import Profile from './pages/Profile';
import Emergency from './pages/Emergency';
import SymptomChecker from './pages/SymptomChecker';
import NotFound from './pages/NotFound';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }}></div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
};

// Public Route (redirect to home if already logged in)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }}></div>
      </div>
    );
  }
  
  return isAuthenticated ? <Navigate to="/" /> : children;
};

// Layout with Navbar and Footer
const Layout = ({ children }) => {
  const location = useLocation();
  const authPages = ['/login', '/register', '/verify-otp'];
  const showNavbar = !authPages.includes(location.pathname);
  const showFooter = !authPages.includes(location.pathname);
  
  return (
    <>
      {showNavbar && <Navbar />}
      <main className={showNavbar ? 'main-content' : ''}>
        {children}
      </main>
      {showFooter && <Footer />}
    </>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Layout>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } />
            <Route path="/register" element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            } />
            <Route path="/verify-otp" element={
              <PublicRoute>
                <VerifyOTP />
              </PublicRoute>
            } />
            
            {/* Home - Accessible to everyone */}
            <Route path="/" element={<Home />} />
            
            {/* Search/Find Doctors */}
            <Route path="/search" element={<SearchDoctors />} />
            <Route path="/doctors" element={<SearchDoctors />} />
            
            {/* Doctor Profile */}
            <Route path="/doctor/:id" element={<DoctorProfile />} />
            
            {/* Emergency Page - Accessible to everyone */}
            <Route path="/emergency" element={<Emergency />} />
            
            {/* Symptom Checker - Accessible to everyone */}
            <Route path="/symptom-checker" element={<SymptomChecker />} />
            
            {/* Protected Routes */}
            <Route path="/profile" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />
            
            <Route path="/appointments" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />
            
            {/* Catch all - 404 Page */}
            <Route path="*" element={<NotFound />} />
          </Routes>
          
          {/* Toast Notifications */}
          <ToastContainer
            position="top-right"
            autoClose={4000}
            hideProgressBar={false}
            newestOnTop
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="light"
          />
        </Layout>
      </Router>
    </AuthProvider>
  );
}

export default App;
