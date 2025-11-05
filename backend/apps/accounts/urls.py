# backend/apps/accounts/urls.py

from django.urls import path
from .views import HealthCheckView, RegisterView # <-- Import our new view

from .views import (
    PatientListView,
    PatientDetailView,
    DoctorProfileView
)

urlpatterns = [
    # When a user visits /api/accounts/health-check/
    # show them the HealthCheckView.
    path('health-check/', HealthCheckView.as_view(), name='health-check'),
    path('register/', RegisterView.as_view(), name='register'),

    # --- Patient Endpoints (Locked) ---
    # GET or POST /api/accounts/patients/
    path('patients/', PatientListView.as_view(), name='patient-list'),
    
    # GET, PUT, or DELETE /api/accounts/patients/1/ (or /2/, etc.)
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),
    
    # --- Doctor Endpoints (Locked) ---
    # GET or PUT /api/accounts/doctor-profile/
    path('doctor-profile/', DoctorProfileView.as_view(), name='doctor-profile'),
]