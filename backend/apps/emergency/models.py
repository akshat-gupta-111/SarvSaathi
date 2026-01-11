from django.db import models
from django.conf import settings
from apps.accounts.models import FamilyMember, DoctorProfile
from apps.appointments.models import Appointment

# Triage choices for emergency categorization
TRIAGE_CHOICES = (
    ('CHEST_PAIN', 'Chest Pain'),
    ('BREATHING', 'Breathing Difficulty'),
    ('INJURY', 'Broken Bone / Injury'),
    ('BLEEDING', 'Severe Bleeding'),
    ('OTHER', 'Other'),
)

class EmergencyRequest(models.Model):
    """
    A log of a single emergency request, from initiation to acceptance.
    """
    
    STATUS_CHOICES = (
        ('SEARCHING', 'Searching for Doctor'),
        ('REQUESTED', 'Request Sent to Doctor'),
        ('ACCEPTED', 'Accepted by Doctor'),
        ('CANCELLED', 'Cancelled by Patient'),
    )

    # Patient (FamilyMember) who made the request
    patient = models.ForeignKey(
        FamilyMember, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="emergency_requests"
    )
    
    # Doctor who accepted (null until accepted)
    doctor = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="emergency_cases"
    )
    
    # The "Special Appointment" that gets created (null until accepted)
    linked_appointment = models.OneToOneField(
        Appointment, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # --- Triage Details ---
    triage_category = models.CharField(max_length=20, choices=TRIAGE_CHOICES)
    patient_notes = models.TextField(blank=True, null=True)
    
    # --- Patient Location ---
    user_lat = models.DecimalField(max_digits=9, decimal_places=6)
    user_lng = models.DecimalField(max_digits=9, decimal_places=6)

    # --- Status ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SEARCHING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emergency_requests'
        ordering = ['-created_at']

    def __str__(self):
        patient_name = self.patient.full_name if self.patient else "Unknown"
        return f"Emergency for {patient_name} ({self.triage_category}) at {self.created_at}"