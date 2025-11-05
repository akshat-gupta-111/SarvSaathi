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
    clinic_address = models.TextField(blank=True)

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.specialty})"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        return relativedelta(date.today(), self.date_of_birth).years