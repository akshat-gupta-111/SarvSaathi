# backend/apps/accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Patient, DoctorProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    When a new CustomUser is "created", this code runs.
    """
    if created: # Only run if the user is new
        if instance.user_type == 'patient':
            # If they're a patient, create a blank "self" record for them
            Patient.objects.create(account_holder=instance, relationship='self')

        elif instance.user_type == 'doctor':
            # If they're a doctor, create a blank DoctorProfile
            DoctorProfile.objects.create(user=instance)