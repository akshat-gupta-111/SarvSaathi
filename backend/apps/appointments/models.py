from django.db import models
from django.conf import settings

# We must import the models from the 'accounts' app to link them
from apps.accounts.models import Patient, DoctorProfile

#
# 1. The TimeSlot Model
# This represents a doctor's availability, not the booking itself.
#
class TimeSlot(models.Model):
    MODE_CHOICES = (
        ('IN_CLINIC', 'In-Clinic'),
        ('ONLINE', 'Online'),
    )

    doctor = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.CASCADE, 
        related_name='time_slots'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # This 'mode' is the trigger for our "token fee" vs "full fee" logic
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='IN_CLINIC')
    
    # When an appointment is booked, this will be set to False
    is_available = models.BooleanField(default=True)

    class Meta:
        # Ensures a doctor can't create two identical time slots
        unique_together = ('doctor', 'start_time', 'end_time')
        ordering = ['start_time']

    def __str__(self):
        # Provides a clean, human-readable name in the admin panel
        doctor_name = self.doctor.user.email # Fallback name
        if self.doctor.first_name:
            doctor_name = f"Dr. {self.doctor.first_name} {self.doctor.last_name}"
        
        return f"{doctor_name} - {self.start_time.strftime('%Y-%m-%d %I:%M %p')} ({self.mode})"

#
# 2. The Appointment Model
# This is the actual booking that links a Patient to a TimeSlot.
#
class Appointment(models.Model):
    # --- Statuses for the entire appointment lifecycle ---
    STATUS_CHOICES = (
        ('PENDING_PAYMENT', 'Pending Payment'), # Initial state
        ('CONFIRMED', 'Confirmed'),           # Payment complete
        ('CANCELLED', 'Cancelled'),           # Cancelled by user or doctor
        ('COMPLETED', 'Completed'),           # Doctor marked as finished
    )
    
    PAYMENT_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
    )

    # --- Core Links ---
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.SET_NULL, # Don't delete appointment if patient is deleted
        null=True, 
        related_name='appointments'
    )
    time_slot = models.OneToOneField(
        TimeSlot, 
        on_delete=models.CASCADE, # If slot is deleted, booking is gone
        related_name='appointment'
    )
    
    # --- Status & Payment Fields ---
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT'
    )
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_CHOICES, default='UNPAID'
    )
    
    # Store the actual amount paid (token or full fee)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    
    # Store the ID from our (dummy) payment gateway
    payment_order_id = models.CharField(max_length=100, blank=True, null=True)

    # --- Fields for ML: Smart Symptom Triage ---
    patient_notes = models.TextField(
        blank=True, null=True, help_text="Symptoms or reason for visit."
    )

    # --- Fields for ML: No-Show Prediction ---
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The 'booking_date' for the ML model."
    )
    reminder_sent = models.BooleanField(
        default=False, help_text="The 'message_sent' for the ML model."
    )

    # --- Fields for ML: Live Wait-Time Prediction ---
    check_in_time = models.DateTimeField(
        null=True, blank=True, help_text="When patient hit 'I am here' in-clinic."
    )
    consultation_start_time = models.DateTimeField(
        null=True, blank=True, help_text="When doctor hits 'Start' button."
    )
    consultation_end_time = models.DateTimeField(
        null=True, blank=True, help_text="When doctor hits 'End' button."
    )
    
    # --- Other details ---
    video_call_link = models.URLField(blank=True, null=True)
    
    class Meta:
        ordering = ['time_slot__start_time'] # Always show appointments in order

    def __str__(self):
        patient_name = self.patient.first_name if self.patient else "Unknown Patient"
        return f"Apt for {patient_name} ({self.status})"
