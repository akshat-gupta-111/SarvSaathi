"""
SarvSaathi - Appointments Models
Robust appointment booking system with proper relationships and audit trails.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


# =============================================================================
# 1. TIME SLOT - Doctor's availability
# =============================================================================

class TimeSlot(models.Model):
    """
    Represents a doctor's available time slot.
    Doctors create these to show when they're available.
    """
    
    MODE_CHOICES = (
        ('in_clinic', 'In-Clinic'),
        ('online', 'Online'),
        ('both', 'Both'),
    )
    
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('blocked', 'Blocked'),  # Doctor blocked this slot
        ('cancelled', 'Cancelled'),
    )
    
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='time_slots'
    )
    
    # --- Time Details ---
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # --- Slot Details ---
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='in_clinic')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    
    # --- Pricing (can override doctor's default) ---
    consultation_fee = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True,
        help_text="Leave empty to use doctor's default fee"
    )
    
    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'time_slots'
        ordering = ['date', 'start_time']
        # Prevent duplicate slots
        unique_together = ('doctor', 'date', 'start_time')
        indexes = [
            models.Index(fields=['doctor', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.doctor.display_name} - {self.date} {self.start_time}-{self.end_time}"
    
    @property
    def is_available(self):
        """Check if slot is available for booking."""
        return self.status == 'available'
    
    @property
    def is_past(self):
        """Check if slot date/time has passed."""
        slot_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        return slot_datetime < timezone.now()
    
    @property
    def effective_fee(self):
        """Get the effective consultation fee for this slot."""
        if self.consultation_fee:
            return self.consultation_fee
        if self.mode == 'online':
            return self.doctor.online_consultation_fee or self.doctor.consultation_fee
        return self.doctor.consultation_fee
    
    def mark_as_booked(self):
        """Mark the slot as booked."""
        self.status = 'booked'
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_as_available(self):
        """Mark the slot as available again (e.g., after cancellation)."""
        self.status = 'available'
        self.save(update_fields=['status', 'updated_at'])


# =============================================================================
# 2. APPOINTMENT - The actual booking
# =============================================================================

class Appointment(models.Model):
    """
    The actual appointment booking linking a patient/family member to a time slot.
    """
    
    STATUS_CHOICES = (
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('paypal', 'PayPal'),
        ('razorpay', 'Razorpay'),
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('free', 'Free/Waived'),
    )
    
    CANCELLATION_REASON_CHOICES = (
        ('patient_request', 'Patient Request'),
        ('doctor_unavailable', 'Doctor Unavailable'),
        ('emergency', 'Emergency'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
        ('other', 'Other'),
    )
    
    # --- Core Relationships ---
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        help_text="The user who booked the appointment"
    )
    
    family_member = models.ForeignKey(
        'accounts.FamilyMember',
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments',
        help_text="The family member this appointment is for"
    )
    
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments'
    )
    
    time_slot = models.OneToOneField(
        TimeSlot,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointment'
    )
    
    # --- Appointment Details ---
    appointment_number = models.CharField(
        max_length=20, unique=True, db_index=True,
        help_text="Unique appointment reference number"
    )
    
    consultation_type = models.CharField(
        max_length=10,
        choices=TimeSlot.MODE_CHOICES,
        default='in_clinic'
    )
    
    # --- Status ---
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # --- Payment ---
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, blank=True)
    
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Payment gateway reference
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_order_id = models.CharField(max_length=100, blank=True, null=True)
    
    # --- Patient Notes & Symptoms ---
    symptoms = models.TextField(blank=True, help_text="Patient's symptoms or reason for visit")
    patient_notes = models.TextField(blank=True, help_text="Additional notes from patient")
    
    # --- Doctor's Notes (after consultation) ---
    doctor_notes = models.TextField(blank=True, help_text="Doctor's notes/observations")
    prescription = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # --- Cancellation ---
    cancellation_reason = models.CharField(max_length=20, choices=CANCELLATION_REASON_CHOICES, blank=True)
    cancellation_notes = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cancelled_appointments'
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # --- Consultation Timing ---
    check_in_time = models.DateTimeField(null=True, blank=True)
    consultation_start_time = models.DateTimeField(null=True, blank=True)
    consultation_end_time = models.DateTimeField(null=True, blank=True)
    
    # --- Online Consultation ---
    video_call_link = models.URLField(blank=True, null=True)
    video_call_id = models.CharField(max_length=100, blank=True)
    
    # --- Reminders ---
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['appointment_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Appointment {self.appointment_number} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Generate appointment number if not set
        if not self.appointment_number:
            self.appointment_number = self._generate_appointment_number()
        super().save(*args, **kwargs)
    
    def _generate_appointment_number(self):
        """Generate a unique appointment number."""
        import random
        import string
        prefix = 'APT'
        timestamp = timezone.now().strftime('%Y%m%d')
        random_suffix = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{timestamp}{random_suffix}"
    
    @property
    def patient_name(self):
        """Get the patient's name (from family_member or user)."""
        if self.family_member:
            return self.family_member.full_name
        return self.user.full_name
    
    @property
    def can_cancel(self):
        """Check if appointment can be cancelled."""
        if self.status in ['cancelled', 'completed', 'no_show']:
            return False
        # Can't cancel if appointment is in less than 2 hours
        if self.time_slot:
            slot_datetime = timezone.make_aware(
                timezone.datetime.combine(self.time_slot.date, self.time_slot.start_time)
            )
            return slot_datetime > timezone.now() + timezone.timedelta(hours=2)
        return False
    
    @property
    def can_reschedule(self):
        """Check if appointment can be rescheduled."""
        return self.status in ['confirmed', 'pending'] and self.can_cancel
    
    def cancel(self, cancelled_by_user, reason='patient_request', notes=''):
        """Cancel the appointment."""
        self.status = 'cancelled'
        self.cancellation_reason = reason
        self.cancellation_notes = notes
        self.cancelled_by = cancelled_by_user
        self.cancelled_at = timezone.now()
        self.save()
        
        # Free up the time slot
        if self.time_slot:
            self.time_slot.mark_as_available()
        
        # Log the cancellation
        AppointmentStatusLog.objects.create(
            appointment=self,
            from_status='confirmed',
            to_status='cancelled',
            changed_by=cancelled_by_user,
            notes=notes
        )
    
    def confirm_payment(self, payment_id, payment_method='paypal'):
        """Confirm payment and update appointment status."""
        self.status = 'confirmed'
        self.payment_status = 'paid'
        self.payment_id = payment_id
        self.payment_method = payment_method
        self.amount_paid = self.consultation_fee
        self.save()
        
        # Mark time slot as booked
        if self.time_slot:
            self.time_slot.mark_as_booked()
        
        # Log the confirmation
        AppointmentStatusLog.objects.create(
            appointment=self,
            from_status='pending',
            to_status='confirmed',
            notes='Payment confirmed'
        )


# =============================================================================
# 3. APPOINTMENT STATUS LOG - Audit trail
# =============================================================================

class AppointmentStatusLog(models.Model):
    """
    Audit trail for appointment status changes.
    Helps track the history of an appointment.
    """
    
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='status_logs'
    )
    
    from_status = models.CharField(max_length=15)
    to_status = models.CharField(max_length=15)
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appointment_status_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.appointment.appointment_number}: {self.from_status} → {self.to_status}"


# =============================================================================
# 4. REVIEW - Patient reviews for doctors
# =============================================================================

class Review(models.Model):
    """
    Patient reviews for doctors after completed appointments.
    """
    
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='review'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # --- Rating (1-5 stars) ---
    rating = models.PositiveSmallIntegerField(
        help_text="Rating from 1 to 5"
    )
    
    # --- Review Text ---
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    
    # --- Specific Ratings ---
    wait_time_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    bedside_manner_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    
    # --- Moderation ---
    is_verified = models.BooleanField(default=True)  # Auto-verified if from completed appointment
    is_visible = models.BooleanField(default=True)
    
    # --- Doctor Response ---
    doctor_response = models.TextField(blank=True)
    doctor_response_at = models.DateTimeField(null=True, blank=True)
    
    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['doctor', 'rating']),
        ]

    def __str__(self):
        return f"Review for {self.doctor.display_name} - {self.rating}/5"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update doctor's average rating
        self._update_doctor_rating()
    
    def _update_doctor_rating(self):
        """Update the doctor's average rating and review count."""
        from django.db.models import Avg, Count
        stats = Review.objects.filter(
            doctor=self.doctor,
            is_visible=True
        ).aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id')
        )
        
        self.doctor.average_rating = stats['avg_rating'] or 0
        self.doctor.total_reviews = stats['total_reviews'] or 0
        self.doctor.save(update_fields=['average_rating', 'total_reviews'])


# =============================================================================
# 5. FAVORITE DOCTOR - Saved doctors
# =============================================================================

class FavoriteDoctor(models.Model):
    """
    User's favorite/saved doctors for quick access.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_doctors'
    )
    
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorite_doctors'
        unique_together = ('user', 'doctor')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.doctor.display_name}"
