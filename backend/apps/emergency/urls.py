from django.urls import path
from .views import FindSpecialistView, RequestDoctorView

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
]