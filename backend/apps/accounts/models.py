"""
SarvSaathi - Accounts Models
Robust, scalable user management system with proper relationships.
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from datetime import timedelta
import random

from .managers import CustomUserManager


# =============================================================================
# 1. CUSTOM USER MODEL - The foundation of our auth system
# =============================================================================

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email as the primary identifier.
    Contains essential user information directly on the user model.
    """
    
    USER_TYPE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )
    
    # --- Primary Fields ---
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # --- Basic Profile (on user for quick access) ---
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # --- User Type & Status ---
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='patient')
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    
    # --- Django Required Fields ---
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # --- Settings ---
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_type']
    
    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Returns the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email.split('@')[0]
    
    def get_full_name(self):
        """Returns the user's full name (method version for compatibility)."""
        return self.full_name
    
    def get_short_name(self):
        """Returns the user's first name."""
        return self.first_name or self.email.split('@')[0]
    
    @property
    def age(self):
        """Calculate age from date of birth."""
        if not self.date_of_birth:
            return None
        return relativedelta(date.today(), self.date_of_birth).years
    
    @property
    def is_profile_complete(self):
        """Check if basic profile is complete."""
        return all([
            self.first_name,
            self.last_name,
            self.phone_number,
            self.date_of_birth,
        ])


# =============================================================================
# 2. USER PROFILE - Extended profile information
# =============================================================================

class UserProfile(models.Model):
    """
    Extended profile information for all users.
    Auto-created when user is created.
    """
    
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # --- Personal Details ---
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    
    # --- Address ---
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='India')
    
    # --- Location (for nearby services) ---
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # --- Preferences ---
    notification_email = models.BooleanField(default=True)
    notification_sms = models.BooleanField(default=True)
    notification_push = models.BooleanField(default=True)
    
    # --- Avatar ---
    avatar_url = models.URLField(blank=True, null=True)
    
    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.email}"
    
    @property
    def full_address(self):
        """Returns formatted full address."""
        parts = filter(None, [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.pincode,
            self.country
        ])
        return ', '.join(parts)


# =============================================================================
# 3. DOCTOR PROFILE - Professional information for doctors
# =============================================================================

class DoctorProfile(models.Model):
    """
    Professional profile for doctors.
    Auto-created when a user registers as doctor.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    
    # --- Professional Details ---
    specialty = models.CharField(max_length=100, blank=True, db_index=True)
    sub_specialty = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    
    # --- Experience & Qualifications ---
    years_of_experience = models.PositiveIntegerField(default=0)
    qualification = models.CharField(max_length=200, blank=True)  # e.g., "MBBS, MD"
    
    # --- Clinic Details ---
    clinic_name = models.CharField(max_length=200, blank=True)
    clinic_address = models.TextField(blank=True)
    clinic_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clinic_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clinic_phone = models.CharField(max_length=15, blank=True)
    
    # --- Consultation Details ---
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    online_consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    consultation_duration = models.PositiveIntegerField(default=15, help_text="Duration in minutes")
    
    # --- Availability ---
    is_available_for_emergency = models.BooleanField(default=False)
    is_accepting_new_patients = models.BooleanField(default=True)
    
    # --- Verification & Status ---
    is_verified = models.BooleanField(default=False, db_index=True)
    verification_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_doctors'
    )
    
    # --- Bio & Description ---
    bio = models.TextField(blank=True, help_text="Short professional bio")
    languages = models.CharField(max_length=200, blank=True, help_text="Comma-separated languages")
    
    # --- Statistics (denormalized for performance) ---
    total_appointments = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_profiles'
        verbose_name = 'Doctor Profile'
        verbose_name_plural = 'Doctor Profiles'
        indexes = [
            models.Index(fields=['specialty']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['consultation_fee']),
            models.Index(fields=['average_rating']),
        ]

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} ({self.specialty})"
    
    @property
    def display_name(self):
        """Returns formatted doctor name."""
        return f"Dr. {self.user.first_name} {self.user.last_name}"
    
    @property
    def is_profile_complete(self):
        """Check if professional profile is complete for verification."""
        required_fields = [
            self.specialty,
            self.license_number,
            self.qualification,
            self.consultation_fee,
            self.clinic_address,
        ]
        return all(required_fields) and self.user.is_profile_complete


# =============================================================================
# 4. DOCTOR EDUCATION - Educational qualifications
# =============================================================================

class DoctorEducation(models.Model):
    """Educational qualifications for doctors."""
    
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='education'
    )
    
    degree = models.CharField(max_length=100)  # e.g., "MBBS", "MD"
    institution = models.CharField(max_length=200)
    year_of_completion = models.PositiveIntegerField()
    
    class Meta:
        db_table = 'doctor_education'
        ordering = ['-year_of_completion']

    def __str__(self):
        return f"{self.degree} - {self.institution} ({self.year_of_completion})"


# =============================================================================
# 5. DOCTOR EXPERIENCE - Work experience
# =============================================================================

class DoctorExperience(models.Model):
    """Work experience for doctors."""
    
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='experiences'
    )
    
    hospital_name = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Null = currently working
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'doctor_experiences'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.position} at {self.hospital_name}"
    
    @property
    def is_current(self):
        return self.end_date is None


# =============================================================================
# 6. FAMILY MEMBER - For booking appointments for family
# =============================================================================

class FamilyMember(models.Model):
    """
    Family members that a user can book appointments for.
    Replaces the old Patient model with better naming and structure.
    """
    
    RELATIONSHIP_CHOICES = (
        ('self', 'Self'),
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    )
    
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='family_members'
    )
    
    # --- Basic Info ---
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    relationship = models.CharField(max_length=10, choices=RELATIONSHIP_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # --- Contact ---
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    
    # --- Medical Info ---
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True, help_text="Known allergies")
    chronic_conditions = models.TextField(blank=True, help_text="Chronic conditions")
    
    # --- Status ---
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'family_members'
        verbose_name = 'Family Member'
        verbose_name_plural = 'Family Members'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relationship})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if not self.date_of_birth:
            return None
        return relativedelta(date.today(), self.date_of_birth).years
    
    @property
    def is_profile_complete(self):
        """Check if profile has minimum required info for booking."""
        return all([
            self.first_name,
            self.phone_number or self.user.phone_number,
        ])


# =============================================================================
# 7. EMERGENCY CONTACT - Contacts to notify in emergency
# =============================================================================

class EmergencyContact(models.Model):
    """Emergency contacts for a user."""
    
    RELATIONSHIP_CHOICES = (
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emergency_contacts'
    )
    
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    email = models.EmailField(blank=True)
    
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emergency_contacts'
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.phone_number}"


# =============================================================================
# 8. MEDICAL RECORD - Health records for users
# =============================================================================

class MedicalRecord(models.Model):
    """Medical records/documents for users."""
    
    RECORD_TYPE_CHOICES = (
        ('prescription', 'Prescription'),
        ('lab_report', 'Lab Report'),
        ('imaging', 'Imaging/Scan'),
        ('discharge_summary', 'Discharge Summary'),
        ('vaccination', 'Vaccination Record'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_records'
    )
    
    family_member = models.ForeignKey(
        FamilyMember,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='medical_records',
        help_text="If record is for a family member"
    )
    
    # --- Record Details ---
    title = models.CharField(max_length=200)
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    description = models.TextField(blank=True)
    record_date = models.DateField()
    
    # --- File Storage ---
    file_url = models.URLField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True)
    
    # --- Doctor/Hospital Info ---
    doctor_name = models.CharField(max_length=200, blank=True)
    hospital_name = models.CharField(max_length=200, blank=True)
    
    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'medical_records'
        ordering = ['-record_date']

    def __str__(self):
        return f"{self.title} - {self.record_date}"


# =============================================================================
# 9. OTP MODEL - For verification
# =============================================================================

class OTP(models.Model):
    """OTPs for email and phone verification."""
    
    OTP_TYPE_CHOICES = (
        ('email', 'Email Verification'),
        ('phone', 'Phone Verification'),
        ('login', 'Login OTP'),
        ('reset_password', 'Reset Password'),
    )
    
    email = models.EmailField(null=True, blank=True, db_index=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True, db_index=True)
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES)
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'otps'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'otp_type']),
            models.Index(fields=['phone_number', 'otp_type']),
        ]

    def __str__(self):
        identifier = self.email or self.phone_number
        return f"OTP for {identifier} ({self.otp_type})"

    @classmethod
    def generate_otp(cls, email=None, phone_number=None, otp_type='email', expires_minutes=10):
        """Generate a 6-digit OTP and save it to the database."""
        # Delete any existing unverified OTPs for this email/phone
        if email:
            cls.objects.filter(email=email, otp_type=otp_type, is_verified=False).delete()
        if phone_number:
            cls.objects.filter(phone_number=phone_number, otp_type=otp_type, is_verified=False).delete()

        # Generate a 6-digit OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # OTP expires in specified minutes
        expires_at = timezone.now() + timedelta(minutes=expires_minutes)

        otp = cls.objects.create(
            email=email,
            phone_number=phone_number,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        return otp

    def is_valid(self):
        """Check if OTP is still valid (not expired, not used, attempts < 3)."""
        return (
            not self.is_verified and 
            timezone.now() < self.expires_at and 
            self.attempts < 3
        )

    def verify(self, code):
        """Verify the OTP code."""
        self.attempts += 1
        self.save()
        
        if self.is_valid() and self.otp_code == code:
            self.is_verified = True
            self.save()
            return True
        return False


# =============================================================================
# SIGNALS - Auto-create related profiles
# =============================================================================

@receiver(post_save, sender=CustomUser)
def create_user_profiles(sender, instance, created, **kwargs):
    """
    Auto-create UserProfile and DoctorProfile (if doctor) when user is created.
    Also create a 'self' FamilyMember for booking.
    """
    if created:
        # Create UserProfile for all users
        UserProfile.objects.get_or_create(user=instance)
        
        # Create DoctorProfile if user is a doctor
        if instance.user_type == 'doctor':
            DoctorProfile.objects.get_or_create(user=instance)
        
        # Create 'self' family member for booking purposes
        FamilyMember.objects.get_or_create(
            user=instance,
            relationship='self',
            defaults={
                'first_name': instance.first_name or 'Self',
                'last_name': instance.last_name or '',
            }
        )


# =============================================================================
# BACKWARD COMPATIBILITY - Alias for old Patient model
# =============================================================================

# This allows existing code using 'Patient' to still work
Patient = FamilyMember
