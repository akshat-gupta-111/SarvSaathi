from django.urls import path
from .views import (
    DoctorTimeSlotListCreateView,
    PatientTimeSlotListView,
)

urlpatterns = [
    # --- Doctor-facing URL ---
    # POST or GET /api/appointments/time-slots/
    path(
        'time-slots/', 
        DoctorTimeSlotListCreateView.as_view(), 
        name='doctor-time-slot-list-create'
    ),
    
    # --- Patient-facing URL ---
    # GET /api/appointments/doctors/<doctor_id>/time-slots/
    path(
        'doctors/<int:doctor_id>/time-slots/', 
        PatientTimeSlotListView.as_view(), 
        name='patient-time-slot-list'
    ),
]