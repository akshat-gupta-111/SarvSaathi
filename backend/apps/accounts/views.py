"""
SarvSaathi - Accounts Views
Clean, organized views for user management.
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from django.conf import settings
import logging
import os

from .models import (
    CustomUser, UserProfile, DoctorProfile, 
    FamilyMember, EmergencyContact, MedicalRecord, OTP
)
from .serializers import (
    UserRegistrationSerializer, RegisterWithOTPSerializer,
    SendOTPSerializer, VerifyOTPSerializer,
    UserDetailSerializer, UserProfileSerializer,
    DoctorProfileSerializer, DoctorListSerializer,
    FamilyMemberSerializer, FamilyMemberListSerializer,
    EmergencyContactSerializer, MedicalRecordSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# OTP UTILITIES
# =============================================================================

def send_otp_email(email, otp_code):
    """Send OTP via email using Gmail SMTP."""
    import smtplib
    import ssl
    from email.message import EmailMessage

    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_APP_PASSWORD")

    if not (sender_email and sender_password):
        logger.warning("Gmail credentials not configured. OTP email not sent.")
        return False

    msg = EmailMessage()
    msg["Subject"] = "SarvSaathi - Your OTP Code"
    msg["From"] = sender_email
    msg["To"] = email
    msg.set_content(f"""
Hello,

Your OTP code for SarvSaathi is: {otp_code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
SarvSaathi Team
    """)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        logger.info(f"OTP email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        return False


def send_otp_sms(phone_number, otp_code):
    """Send OTP via SMS using Twilio."""
    try:
        from twilio.rest import Client
    except ImportError:
        logger.warning("Twilio not installed. OTP SMS not sent.")
        return False

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_FROM_NUMBER")

    if not (sid and token and from_num):
        logger.warning("Twilio credentials not configured. OTP SMS not sent.")
        return False

    try:
        client = Client(sid, token)
        client.messages.create(
            body=f"Your SarvSaathi OTP code is: {otp_code}. Valid for 10 minutes.",
            from_=from_num,
            to=phone_number
        )
        logger.info(f"OTP SMS sent to {phone_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP SMS: {e}")
        return False


# =============================================================================
# HEALTH CHECK
# =============================================================================

class HealthCheckView(APIView):
    """API health check endpoint."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "status": "healthy",
            "message": "SarvSaathi API is live and healthy!",
            "version": "2.0"
        })


# =============================================================================
# AUTHENTICATION VIEWS
# =============================================================================

class RegisterView(generics.CreateAPIView):
    """User registration without OTP."""
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer


class RegisterWithOTPView(generics.CreateAPIView):
    """User registration with OTP verification."""
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterWithOTPSerializer


class SendOTPView(APIView):
    """Send OTP to email or phone number."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get('email')
        phone_number = serializer.validated_data.get('phone_number')
        otp_type = serializer.validated_data.get('otp_type', 'email')

        # Generate OTP
        otp = OTP.generate_otp(
            email=email,
            phone_number=phone_number,
            otp_type=otp_type
        )

        # Send OTP
        sent = False
        if email:
            sent = send_otp_email(email, otp.otp_code)
        elif phone_number:
            sent = send_otp_sms(phone_number, otp.otp_code)

        response_data = {
            "message": "OTP sent successfully" if sent else "OTP generated (check logs for delivery status)",
            "expires_in_minutes": 10,
        }

        # In development mode, include OTP for testing
        if settings.DEBUG:
            response_data["otp_code"] = otp.otp_code
            response_data["debug_note"] = "OTP included for testing only."

        return Response(response_data, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """Verify OTP code."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get('email')
        phone_number = serializer.validated_data.get('phone_number')
        otp_code = serializer.validated_data.get('otp_code')
        otp_type = serializer.validated_data.get('otp_type', 'email')

        try:
            filters = {'otp_type': otp_type, 'is_verified': False}
            if email:
                filters['email'] = email
            if phone_number:
                filters['phone_number'] = phone_number

            otp = OTP.objects.filter(**filters).latest('created_at')

            if otp.verify(otp_code):
                return Response({
                    "message": "OTP verified successfully",
                    "verified": True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "Invalid or expired OTP",
                    "verified": False
                }, status=status.HTTP_400_BAD_REQUEST)

        except OTP.DoesNotExist:
            return Response({
                "message": "No OTP found. Please request a new one.",
                "verified": False
            }, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# USER PROFILE VIEWS
# =============================================================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get or update the logged-in user's profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    def get_object(self):
        return self.request.user


class UserProfileOnlyView(generics.RetrieveUpdateAPIView):
    """Get or update the extended profile only."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user.profile


# =============================================================================
# DOCTOR VIEWS
# =============================================================================

class DoctorProfileView(generics.RetrieveUpdateAPIView):
    """Get or update the logged-in doctor's profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = DoctorProfileSerializer

    def get_object(self):
        if self.request.user.user_type != 'doctor':
            raise NotFound("Doctor profile not available for this account type.")
        try:
            return self.request.user.doctor_profile
        except DoctorProfile.DoesNotExist:
            raise NotFound("Doctor profile not set up yet.")


class VerifiedDoctorListView(generics.ListAPIView):
    """Public listing of verified doctors."""
    permission_classes = [AllowAny]
    serializer_class = DoctorListSerializer

    def get_queryset(self):
        queryset = DoctorProfile.objects.filter(is_verified=True).select_related('user')
        
        # Filter by specialty
        specialty = self.request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
        
        # Filter by fee range
        min_fee = self.request.query_params.get('min_fee')
        max_fee = self.request.query_params.get('max_fee')
        if min_fee:
            queryset = queryset.filter(consultation_fee__gte=min_fee)
        if max_fee:
            queryset = queryset.filter(consultation_fee__lte=max_fee)
        
        # Filter by experience
        min_exp = self.request.query_params.get('min_experience')
        if min_exp:
            queryset = queryset.filter(years_of_experience__gte=min_exp)
        
        # Sort
        sort_by = self.request.query_params.get('sort', '-average_rating')
        valid_sorts = ['average_rating', '-average_rating', 'consultation_fee', '-consultation_fee', 'years_of_experience', '-years_of_experience']
        if sort_by in valid_sorts:
            queryset = queryset.order_by(sort_by)
        
        return queryset


class DoctorDetailView(generics.RetrieveAPIView):
    """Public view for a single doctor's profile."""
    permission_classes = [AllowAny]
    serializer_class = DoctorProfileSerializer
    queryset = DoctorProfile.objects.filter(is_verified=True).select_related('user')


# =============================================================================
# FAMILY MEMBER VIEWS
# =============================================================================

class FamilyMemberListCreateView(generics.ListCreateAPIView):
    """List and create family members for logged-in user."""
    permission_classes = [IsAuthenticated]
    serializer_class = FamilyMemberSerializer

    def get_queryset(self):
        return FamilyMember.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FamilyMemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a family member."""
    permission_classes = [IsAuthenticated]
    serializer_class = FamilyMemberSerializer

    def get_queryset(self):
        return FamilyMember.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        # Soft delete - don't actually delete
        instance.is_active = False
        instance.save()


class FamilyMemberListOnlyView(generics.ListAPIView):
    """Simplified list for dropdowns."""
    permission_classes = [IsAuthenticated]
    serializer_class = FamilyMemberListSerializer

    def get_queryset(self):
        return FamilyMember.objects.filter(user=self.request.user, is_active=True)


# =============================================================================
# EMERGENCY CONTACT VIEWS
# =============================================================================

class EmergencyContactListCreateView(generics.ListCreateAPIView):
    """List and create emergency contacts."""
    permission_classes = [IsAuthenticated]
    serializer_class = EmergencyContactSerializer

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EmergencyContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete an emergency contact."""
    permission_classes = [IsAuthenticated]
    serializer_class = EmergencyContactSerializer

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)


# =============================================================================
# MEDICAL RECORD VIEWS
# =============================================================================

class MedicalRecordListCreateView(generics.ListCreateAPIView):
    """List and create medical records."""
    permission_classes = [IsAuthenticated]
    serializer_class = MedicalRecordSerializer

    def get_queryset(self):
        return MedicalRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MedicalRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a medical record."""
    permission_classes = [IsAuthenticated]
    serializer_class = MedicalRecordSerializer

    def get_queryset(self):
        return MedicalRecord.objects.filter(user=self.request.user)


# =============================================================================
# AVATAR UPLOAD VIEW
# =============================================================================

class AvatarUploadView(APIView):
    """Upload or update user avatar to Cloudinary."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .cloudinary_utils import upload_avatar
        
        if 'avatar' not in request.FILES:
            return Response(
                {"error": "No avatar image provided. Please upload an image file."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        avatar_file = request.FILES['avatar']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if avatar_file.content_type not in allowed_types:
            return Response(
                {"error": f"Invalid file type. Allowed types: {', '.join(allowed_types)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if avatar_file.size > max_size:
            return Response(
                {"error": "File too large. Maximum size is 5MB."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Upload to Cloudinary
        avatar_url = upload_avatar(avatar_file, request.user.id)
        
        if not avatar_url:
            return Response(
                {"error": "Failed to upload avatar. Please check Cloudinary configuration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update user profile with new avatar URL
        profile = request.user.profile
        profile.avatar_url = avatar_url
        profile.save()
        
        logger.info(f"Avatar uploaded for user {request.user.email}")
        
        return Response({
            "message": "Avatar uploaded successfully",
            "avatar_url": avatar_url
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        """Remove user avatar."""
        from .cloudinary_utils import delete_image_from_cloudinary
        
        profile = request.user.profile
        
        if not profile.avatar_url:
            return Response(
                {"message": "No avatar to remove"},
                status=status.HTTP_200_OK
            )
        
        # Try to delete from Cloudinary
        public_id = f"sarvsaathi/avatars/user_{request.user.id}_avatar"
        delete_image_from_cloudinary(public_id)
        
        # Clear avatar URL from profile
        profile.avatar_url = None
        profile.save()
        
        logger.info(f"Avatar removed for user {request.user.email}")
        
        return Response({
            "message": "Avatar removed successfully"
        }, status=status.HTTP_200_OK)


# =============================================================================
# BACKWARD COMPATIBILITY - Aliases for old views
# =============================================================================

# These maintain backward compatibility with existing URLs
PatientListView = FamilyMemberListCreateView
PatientDetailView = FamilyMemberDetailView
