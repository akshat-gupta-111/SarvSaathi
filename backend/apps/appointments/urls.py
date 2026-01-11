"""
SarvSaathi - Appointments URLs
Clean, organized URL routing for appointment system.
"""

from django.urls import path
from .views import (
    # Time slots
    DoctorTimeSlotListCreateView,
    DoctorTimeSlotDetailView,
    PublicTimeSlotListView,
    BulkTimeSlotCreateView,
    
    # Patient appointments
    AppointmentCreateView,
    AppointmentListView,
    AppointmentDetailView,
    AppointmentCancelView,
    
    # Doctor appointments
    DoctorAppointmentListView,
    DoctorAppointmentDetailView,
    DoctorAppointmentNotesView,
    DoctorCancelAppointmentView,
    DoctorCompleteAppointmentView,
    DoctorStartConsultationView,
    
    # Payments
    InitiatePaymentView,
    ExecutePaymentView,
    ConfirmAppointmentView,
    
    # Reviews
    ReviewCreateView,
    ReviewListView,
    MyReviewsView,
    DoctorReviewResponseView,
    
    # Favorites
    FavoriteDoctorListView,
    FavoriteDoctorToggleView,
    CheckFavoriteView,
    
    # Stats
    AppointmentStatsView,
)

app_name = 'appointments'

urlpatterns = [
    # ==========================================================================
    # TIME SLOTS - Doctor Management
    # ==========================================================================
    # Doctor creates/lists their time slots
    path('time-slots/', DoctorTimeSlotListCreateView.as_view(), name='doctor-timeslot-list'),
    path('time-slots/<int:pk>/', DoctorTimeSlotDetailView.as_view(), name='doctor-timeslot-detail'),
    path('time-slots/bulk/', BulkTimeSlotCreateView.as_view(), name='timeslot-bulk-create'),
    
    # ==========================================================================
    # TIME SLOTS - Public/Patient View
    # ==========================================================================
    # Patient views available slots for a doctor
    path('doctors/<int:doctor_id>/time-slots/', PublicTimeSlotListView.as_view(), name='doctor-available-slots'),
    
    # ==========================================================================
    # APPOINTMENTS - Patient
    # ==========================================================================
    # Book appointment
    path('book/', AppointmentCreateView.as_view(), name='appointment-create'),
    
    # List patient's appointments
    path('my-appointments/', AppointmentListView.as_view(), name='my-appointments'),
    
    # View appointment details
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    
    # Cancel appointment
    path('appointments/<int:pk>/cancel/', AppointmentCancelView.as_view(), name='appointment-cancel'),
    
    # ==========================================================================
    # APPOINTMENTS - Doctor
    # ==========================================================================
    # Doctor's appointment list
    path('doctor/appointments/', DoctorAppointmentListView.as_view(), name='doctor-appointments'),
    path('doctor/appointments/<int:pk>/', DoctorAppointmentDetailView.as_view(), name='doctor-appointment-detail'),
    path('doctor/appointments/<int:pk>/notes/', DoctorAppointmentNotesView.as_view(), name='doctor-appointment-notes'),
    path('doctor/appointments/<int:pk>/cancel/', DoctorCancelAppointmentView.as_view(), name='doctor-cancel-appointment'),
    path('doctor/appointments/<int:pk>/complete/', DoctorCompleteAppointmentView.as_view(), name='doctor-complete-appointment'),
    path('doctor/appointments/<int:pk>/start/', DoctorStartConsultationView.as_view(), name='doctor-start-consultation'),
    
    # ==========================================================================
    # PAYMENTS
    # ==========================================================================
    # Initiate PayPal payment
    path('appointments/<int:pk>/pay/', InitiatePaymentView.as_view(), name='initiate-payment'),
    
    # Execute payment after PayPal approval
    path('appointments/<int:pk>/execute-payment/', ExecutePaymentView.as_view(), name='execute-payment'),
    
    # Manual confirmation (for testing)
    path('appointments/<int:pk>/confirm/', ConfirmAppointmentView.as_view(), name='confirm-appointment'),
    
    # ==========================================================================
    # REVIEWS
    # ==========================================================================
    path('reviews/', ReviewCreateView.as_view(), name='review-create'),
    path('reviews/my/', MyReviewsView.as_view(), name='my-reviews'),
    path('doctors/<int:doctor_id>/reviews/', ReviewListView.as_view(), name='doctor-reviews'),
    path('reviews/<int:pk>/respond/', DoctorReviewResponseView.as_view(), name='review-respond'),
    
    # ==========================================================================
    # FAVORITES
    # ==========================================================================
    path('favorites/', FavoriteDoctorListView.as_view(), name='favorite-list'),
    path('favorites/<int:doctor_id>/toggle/', FavoriteDoctorToggleView.as_view(), name='favorite-toggle'),
    path('favorites/<int:doctor_id>/check/', CheckFavoriteView.as_view(), name='favorite-check'),
    
    # ==========================================================================
    # STATISTICS
    # ==========================================================================
    path('stats/', AppointmentStatsView.as_view(), name='appointment-stats'),
]
