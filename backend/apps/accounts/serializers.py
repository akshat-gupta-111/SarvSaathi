# backend/apps/accounts/serializers.py

from rest_framework import serializers



# --- IMPORT YOUR NEW MODELS ---
from .models import CustomUser, Patient, DoctorProfile
from datetime import date
from dateutil.relativedelta import relativedelta

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    A serializer for creating new users.
    It ensures the password is write-only (never readable) and is hashed.
    """
    
    # We make 'password' write-only. This means when we send user data
    # back from the API, we will *never* include the password.
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        
        # These are the fields the API will accept when creating a user
        fields = ('email', 'password', 'user_type')

    def create(self, validated_data):
        # This 'create' method is the magic.
        # We use our custom manager's 'create_user' function
        # which handles all the password hashing for us.
        
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'patient') # Default to 'patient'
        )
        return user
    

# backend/apps/accounts/serializers.py



# ... (your UserRegistrationSerializer is already here) ...


# --- ADD THIS NEW SERIALIZER ---
class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Patient model.
    Handles the "family account" and "self" records.
    """
    # These are "read-only" fields calculated by the model
    age = serializers.IntegerField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = Patient
        # These are all the fields the API will show or accept
        fields = (
            'id', 'account_holder', 'relationship', 'first_name', 'last_name', 
            'date_of_birth', 'email', 'phone_number', 'address', 'age', 'is_complete'
        )
        # The user can't change who the account holder is
        read_only_fields = ('account_holder',)

    def validate_date_of_birth(self, value):
        """
        This is where your 18+ validation logic runs!
        """
        if not value:
            # Don't validate if it's empty
            return value

        # Calculate age
        age = relativedelta(date.today(), value).years
        
        # We need to know the relationship for this patient
        # 'self.instance' is the patient being updated (if it exists)
        relationship = self.instance.relationship if self.instance else self.initial_data.get('relationship')
        
        # --- THIS IS THE 18+ LOGIC ---
        # We only enforce 18+ for the "self" record (the account holder)
        # Children (or other relatives) can be any age.
        if relationship == 'self' and age < 18:
            raise serializers.ValidationError("Account holders must be 18 years or older.")
            
        return value

# (Your UserRegistrationSerializer and PatientSerializer are already in this file)
# ...

# --- REPLACE YOUR OLD DoctorProfileSerializer WITH THIS ---
class DoctorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Doctor's professional profile.
    """
    age = serializers.IntegerField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    
    # NEW: We can also get the email from the linked user,
    # which is useful for the frontend.
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = DoctorProfile
        
        # --- MODIFICATION ---
        # Add 'latitude' and 'longitude' to this list
        fields = (
            'id', 'user', 'email', 'first_name', 'last_name', 'date_of_birth', 
            'phone_number', 'specialty', 'license_number', 
            'consultation_fee', 'clinic_address', 
            'latitude', 'longitude', # <-- HERE
            'age', 'is_complete', 'is_verified'
        )
        # --- END MODIFICATION ---
        
        read_only_fields = ('user', 'is_verified', 'is_complete')

    def validate_date_of_birth(self, value):
        # We can also add an age check for doctors
        if not value:
            return value
        age = relativedelta(date.today(), value).years
        if age < 21: # A reasonable minimum age for a doctor
            raise serializers.ValidationError("Doctors must be at least 21 years old.")
        return value