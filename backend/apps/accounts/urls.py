"""
SarvSaathi - Accounts URLs
Clean, organized URL routing for user management.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    # Health check
    HealthCheckView,
    
    # Authentication
    RegisterView,
    RegisterWithOTPView,
    SendOTPView,
    VerifyOTPView,
    
    # User profile
    UserProfileView,
    UserProfileOnlyView,
    
    # Doctor
    DoctorProfileView,
    VerifiedDoctorListView,
    DoctorDetailView,
    
    # Family members (replaces patients)
    FamilyMemberListCreateView,
    FamilyMemberDetailView,
    FamilyMemberListOnlyView,
    
    # Emergency contacts
    EmergencyContactListCreateView,
    EmergencyContactDetailView,
    
    # Medical records
    MedicalRecordListCreateView,
    MedicalRecordDetailView,
)

app_name = 'accounts'

urlpatterns = [
    # ==========================================================================
    # HEALTH CHECK
    # ==========================================================================
    path('health-check/', HealthCheckView.as_view(), name='health-check'),
    
    # ==========================================================================
    # AUTHENTICATION
    # ==========================================================================
    # JWT Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Registration
    path('register/', RegisterView.as_view(), name='register'),
    path('register-with-otp/', RegisterWithOTPView.as_view(), name='register-with-otp'),
    
    # OTP
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    
    # ==========================================================================
    # USER PROFILE
    # ==========================================================================
    # Get/update current user details (includes profile)
    path('me/', UserProfileView.as_view(), name='user-detail'),
    path('profile/', UserProfileOnlyView.as_view(), name='user-profile'),
    
    # ==========================================================================
    # DOCTORS
    # ==========================================================================
    # For logged-in doctor to manage their own profile
    path('doctor-profile/', DoctorProfileView.as_view(), name='doctor-profile'),
    
    # Public doctor listings
    path('doctors/', VerifiedDoctorListView.as_view(), name='doctor-list'),
    path('doctors/verified/', VerifiedDoctorListView.as_view(), name='verified-doctor-list'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    
    # ==========================================================================
    # FAMILY MEMBERS (was Patients)
    # ==========================================================================
    path('family-members/', FamilyMemberListCreateView.as_view(), name='family-member-list'),
    path('family-members/<int:pk>/', FamilyMemberDetailView.as_view(), name='family-member-detail'),
    path('family-members/list/', FamilyMemberListOnlyView.as_view(), name='family-member-simple-list'),
    
    # Backward compatibility - keep old patient URLs working
    path('patients/', FamilyMemberListCreateView.as_view(), name='patient-list'),
    path('patients/<int:pk>/', FamilyMemberDetailView.as_view(), name='patient-detail'),
    
    # ==========================================================================
    # EMERGENCY CONTACTS
    # ==========================================================================
    path('emergency-contacts/', EmergencyContactListCreateView.as_view(), name='emergency-contact-list'),
    path('emergency-contacts/<int:pk>/', EmergencyContactDetailView.as_view(), name='emergency-contact-detail'),
    
    # ==========================================================================
    # MEDICAL RECORDS
    # ==========================================================================
    path('medical-records/', MedicalRecordListCreateView.as_view(), name='medical-record-list'),
    path('medical-records/<int:pk>/', MedicalRecordDetailView.as_view(), name='medical-record-detail'),
]
