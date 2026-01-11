"""
SarvSaathi - Appointment Permissions
Custom permission classes for the appointments app.
"""

from rest_framework.permissions import BasePermission


class IsDoctor(BasePermission):
    """
    Permission to only allow users with the 'doctor' user_type.
    """
    message = "You must be a doctor to access this resource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == 'doctor'


class IsPatient(BasePermission):
    """
    Permission to only allow users with the 'patient' user_type.
    """
    message = "You must be a patient to access this resource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == 'patient'


class IsAppointmentOwner(BasePermission):
    """
    Permission to only allow the owner (patient) of an appointment to access it.
    """
    message = "You can only access your own appointments."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsAppointmentDoctor(BasePermission):
    """
    Permission to only allow the doctor of an appointment to access it.
    """
    message = "You can only access appointments assigned to you."

    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'doctor_profile'):
            return False
        return obj.doctor == request.user.doctor_profile


class IsReviewOwner(BasePermission):
    """
    Permission to only allow the owner of a review to modify it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user