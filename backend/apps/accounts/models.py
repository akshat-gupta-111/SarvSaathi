from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


from django.conf import settings # <-- IMPORT THIS
from datetime import date # <-- IMPORT THIS
from dateutil.relativedelta import relativedelta # <-- IMPORT THIS

from .managers import CustomUserManager

# We import our new manager
from .managers import CustomUserManager

class CustomUser(AbstractBaseUser, PermissionsMixin):
    
    # --- Our Fields ---
    email = models.EmailField(unique=True) # This is now the login ID

    USER_TYPE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='patient')
    
    # These fields are required by Django's admin
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # --- The "Magic" ---
    
    # 1. This is the field that will be used for logging in
    USERNAME_FIELD = 'email'
    
    # 2. These fields will be asked for when creating a superuser
    REQUIRED_FIELDS = ['user_type'] # email & password are required by default
    
    # 3. This tells our model to use the manager we just built
    objects = CustomUserManager()

    def __str__(self):
        return self.email
    

# backend/apps/accounts/models.py





# --- ADD THIS NEW MODEL ---
class Patient(models.Model):
    # This is the "Family" link. One User (Account Holder) can have MANY patients
    account_holder = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="patients"
    )
    
    # This is how you'll handle the "book for me" vs "book for child"
    RELATIONSHIP_CHOICES = (
        ('self', 'Self'),
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('other', 'Other'),
    )
    relationship = models.CharField(max_length=10, choices=RELATIONSHIP_CHOICES, default='self')
    
    # --- This is the Patient's actual data ---
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    phone_number = models.CharField(max_length=15, blank=True)
    # email is for communication, but NOT for login
    email = models.EmailField(blank=True) 
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relationship})"

    # This is a "calculated" field for the 18+ check
    @property
    def age(self):
        if not self.date_of_birth:
            return None
        return relativedelta(date.today(), self.date_of_birth).years

    # This is your "is profile complete?" logic
    @property
    def is_complete(self):
        # We define "complete" as having all these key fields
        return all([
            self.first_name,
            self.last_name,
            self.date_of_birth,
            self.phone_number,
            self.email
        ])

# --- ADD THIS NEW MODEL ---
# (Your CustomUser and Patient models are already above this)
# ...

class DoctorProfile(models.Model):
    # This is a one-to-one link. One User has ONE Doctor Profile.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="doctor_profile"
    )
    
    # --- This is the Doctor's actual data ---
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    specialty = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # --- MODIFICATION START ---
    
    # We've kept clinic_address
    clinic_address = models.TextField(blank=True)
    
    # NEW: Added latitude for mapping
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    # NEW: Added longitude for mapping
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    # --- MODIFICATION END ---
    
    # Admin toggles this when a doctor's profile has been reviewed manually.
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.specialty})"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        return relativedelta(date.today(), self.date_of_birth).years

    @property
    def is_complete(self):
        """Return True when the profile has all mandatory professional details."""
        
        # --- MODIFICATION START ---
        # We've changed this to be safer.
        # An empty string (like '') is "truthy" in a list, but it's not complete.
        # We must check `is not None` for numbers/decimals and non-empty for text.
        
        # 1. Check all text fields
        mandatory_text_values = [
            self.first_name,
            self.last_name,
            self.phone_number,
            self.specialty,
            self.license_number,
            self.clinic_address,
        ]
        
        # 2. Check all date/number fields
        is_dob_provided = self.date_of_birth is not None
        is_fee_provided = self.consultation_fee is not None
        
        # NEW: Check our new location fields
        is_lat_provided = self.latitude is not None
        is_lon_provided = self.longitude is not None

        # The profile is complete ONLY if all text fields are non-empty
        # AND all number/date/location fields are provided.
        return (
            all(bool(value and value.strip()) for value in mandatory_text_values) and
            is_dob_provided and
            is_fee_provided and
            is_lat_provided and
            is_lon_provided
        )
        # --- MODIFICATION END ---