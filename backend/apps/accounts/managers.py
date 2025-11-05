# This file tells Django how to create users where email is the ID
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    A custom user manager for creating users with an email instead of a username.
    """
    
    # This function is for creating a REGULAR user
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        
        # "Normalize" the email (e.g., converts 'Test@GMAIL.COM' to 'test@gmail.com')
        email = self.normalize_email(email)
        
        # Create the user object
        user = self.model(email=email, **extra_fields)
        
        # Set the (hashed) password
        user.set_password(password)
        
        # Save the user to the database
        user.save(using=self._db)
        return user

    # This function is for creating a SUPER user (for the admin panel)
    def create_superuser(self, email, password=None, **extra_fields):
        # Superusers must have these flags set to True
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Use the regular create_user function to do the work
        return self.create_user(email, password, **extra_fields)