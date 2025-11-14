from rest_framework.permissions import BasePermission

class IsDoctor(BasePermission):
    """
    A custom permission to only allow users with the 'doctor' user_type.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if the authenticated user is a 'doctor'
        return request.user.user_type == 'doctor'