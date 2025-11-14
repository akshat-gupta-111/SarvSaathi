from django.urls import path
from .views import (
    DoctorTimeSlotListCreateView,
    PatientTimeSlotListView,
    AppointmentCreateView,      # NEW: Import the booking view
    AppointmentExecuteView,     # NEW: Import the execute view
    AppointmentCancelView,      # NEW: Import the cancel view
)

urlpatterns = [
    # --- Phase 1 URLs (Already here) ---
    
    # Doctor-facing URL
    # POST or GET /api/appointments/time-slots/
    path(
        'time-slots/', 
        DoctorTimeSlotListCreateView.as_view(), 
        name='doctor-time-slot-list-create'
    ),
    
    # Patient-facing URL
    # GET /api/appointments/doctors/<doctor_id>/time-slots/
    path(
        'doctors/<int:doctor_id>/time-slots/', 
        PatientTimeSlotListView.as_view(), 
        name='patient-time-slot-list'
    ),

    # --- Phase 2: PayPal Booking URLs (NEW) ---

    # Stage 1: Patient starts the booking
    # POST /api/appointments/book/
    path(
        'book/', 
        AppointmentCreateView.as_view(), 
        name='appointment-create'
    ),

    # Stage 3: Frontend sends paymentId/PayerID here
    # POST /api/appointments/execute-payment/
    path(
        'execute-payment/', 
        AppointmentExecuteView.as_view(), 
        name='appointment-execute'
    ),

    # Stage 3b: User is sent here if they cancel on PayPal
    # GET /api/appointments/cancel-payment/
    path(
        'cancel-payment/', 
        AppointmentCancelView.as_view(), 
        name='appointment-cancel'
    ),
]