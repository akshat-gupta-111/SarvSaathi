from django.urls import path
from .views import FindSpecialistView, RequestDoctorView, TriggerSOSView, NearbyHospitalsView

app_name = 'emergency'

urlpatterns = [
    # Step 1: POST /api/emergency/find-specialist/
    path(
        'find-specialist/', 
        FindSpecialistView.as_view(), 
        name='emergency-find-specialist'
    ),
    
    # Step 2: POST /api/emergency/request-doctor/
    path(
        'request-doctor/', 
        RequestDoctorView.as_view(), 
        name='emergency-request-doctor'
    ),
    
    # SOS Alert: POST /api/emergency/trigger-sos/
    path(
        'trigger-sos/',
        TriggerSOSView.as_view(),
        name='trigger-sos'
    ),
    
    # Nearby Hospitals: GET /api/emergency/hospitals/
    path(
        'hospitals/',
        NearbyHospitalsView.as_view(),
        name='nearby-hospitals'
    ),
]