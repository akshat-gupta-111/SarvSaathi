"""
SarvSaathi - Appointments Views
Robust views for appointment booking system.
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, NotFound
from django.utils import timezone
from django.db.models import Q
import paypalrestsdk
import logging
import os

from .models import TimeSlot, Appointment, Review, FavoriteDoctor
from .serializers import (
    TimeSlotCreateSerializer, TimeSlotListSerializer, TimeSlotDetailSerializer,
    AppointmentCreateSerializer, AppointmentPaymentSerializer, AppointmentConfirmSerializer,
    AppointmentListSerializer, AppointmentDetailSerializer, DoctorAppointmentSerializer,
    AppointmentCancelSerializer, AppointmentDoctorNotesSerializer,
    ReviewCreateSerializer, ReviewListSerializer, ReviewDoctorResponseSerializer,
    FavoriteDoctorSerializer,
)
from .permissions import IsDoctor, IsPatient

logger = logging.getLogger(__name__)


# =============================================================================
# PAYPAL CONFIGURATION
# =============================================================================

def configure_paypal():
    """Configure PayPal SDK."""
    mode = os.getenv("PAYPAL_MODE", "sandbox")
    client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "")
    
    paypalrestsdk.configure({
        "mode": mode,
        "client_id": client_id,
        "client_secret": client_secret
    })


# =============================================================================
# TIME SLOT VIEWS
# =============================================================================

class DoctorTimeSlotListCreateView(generics.ListCreateAPIView):
    """Doctor manages their time slots."""
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TimeSlotCreateSerializer
        return TimeSlotListSerializer

    def get_queryset(self):
        return TimeSlot.objects.filter(
            doctor=self.request.user.doctor_profile
        ).order_by('date', 'start_time')

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor_profile)


class DoctorTimeSlotDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Doctor manages a specific time slot."""
    permission_classes = [IsAuthenticated, IsDoctor]
    serializer_class = TimeSlotDetailSerializer

    def get_queryset(self):
        return TimeSlot.objects.filter(doctor=self.request.user.doctor_profile)


class PublicTimeSlotListView(generics.ListAPIView):
    """Public list of available time slots for a doctor."""
    permission_classes = [AllowAny]
    serializer_class = TimeSlotListSerializer

    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        today = timezone.now().date()
        
        return TimeSlot.objects.filter(
            doctor_id=doctor_id,
            date__gte=today,
            status='available'
        ).order_by('date', 'start_time')


class BulkTimeSlotCreateView(APIView):
    """Create multiple time slots at once."""
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        slots_data = request.data.get('slots', [])
        if not slots_data:
            return Response(
                {"error": "No slots provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        doctor_profile = request.user.doctor_profile
        created_slots = []
        errors = []

        for slot_data in slots_data:
            slot_data['doctor'] = doctor_profile.id
            serializer = TimeSlotCreateSerializer(data=slot_data)
            if serializer.is_valid():
                slot = serializer.save(doctor=doctor_profile)
                created_slots.append(TimeSlotListSerializer(slot).data)
            else:
                errors.append({
                    "data": slot_data,
                    "errors": serializer.errors
                })

        return Response({
            "created": len(created_slots),
            "slots": created_slots,
            "errors": errors
        }, status=status.HTTP_201_CREATED if created_slots else status.HTTP_400_BAD_REQUEST)


# =============================================================================
# APPOINTMENT VIEWS
# =============================================================================

class AppointmentCreateView(generics.CreateAPIView):
    """Create a new appointment."""
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AppointmentListView(generics.ListAPIView):
    """List appointments for logged-in patient."""
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentListSerializer

    def get_queryset(self):
        queryset = Appointment.objects.filter(user=self.request.user)
        
        # Filter by status
        appointment_status = self.request.query_params.get('status')
        if appointment_status:
            queryset = queryset.filter(status=appointment_status)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(time_slot__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(time_slot__date__lte=to_date)
        
        # Sort
        sort_by = self.request.query_params.get('sort', '-created_at')
        return queryset.order_by(sort_by)


class AppointmentDetailView(generics.RetrieveAPIView):
    """Get appointment details."""
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentDetailSerializer

    def get_queryset(self):
        return Appointment.objects.filter(
            Q(user=self.request.user) | Q(doctor__user=self.request.user)
        )


class AppointmentCancelView(APIView):
    """Cancel an appointment."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk, user=request.user)
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found")

        if not appointment.can_cancel:
            return Response(
                {"error": "This appointment cannot be cancelled. Cancellation is only allowed more than 24 hours before the appointment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AppointmentCancelSerializer(data=request.data)
        if serializer.is_valid():
            reason = serializer.validated_data.get('cancellation_reason', '')
            cancelled_by = 'patient'
            
            appointment.cancel(cancelled_by=cancelled_by, reason=reason)
            
            return Response({
                "message": "Appointment cancelled successfully",
                "appointment": AppointmentDetailSerializer(appointment).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# DOCTOR APPOINTMENT VIEWS
# =============================================================================

class DoctorAppointmentListView(generics.ListAPIView):
    """List appointments for logged-in doctor."""
    permission_classes = [IsAuthenticated, IsDoctor]
    serializer_class = DoctorAppointmentSerializer

    def get_queryset(self):
        queryset = Appointment.objects.filter(
            doctor=self.request.user.doctor_profile
        )
        
        # Filter by status
        appointment_status = self.request.query_params.get('status')
        if appointment_status:
            queryset = queryset.filter(status=appointment_status)
        
        # Filter by date
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(time_slot__date=date)
        
        # Default: today's and future appointments
        show_past = self.request.query_params.get('show_past', 'false').lower() == 'true'
        if not show_past:
            today = timezone.now().date()
            queryset = queryset.filter(time_slot__date__gte=today)
        
        return queryset.order_by('time_slot__date', 'time_slot__start_time')


class DoctorAppointmentDetailView(generics.RetrieveUpdateAPIView):
    """Doctor views and updates appointment."""
    permission_classes = [IsAuthenticated, IsDoctor]
    serializer_class = DoctorAppointmentSerializer

    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user.doctor_profile)


class DoctorAppointmentNotesView(APIView):
    """Doctor adds notes to appointment."""
    permission_classes = [IsAuthenticated, IsDoctor]

    def patch(self, request, pk):
        try:
            appointment = Appointment.objects.get(
                pk=pk, 
                doctor=request.user.doctor_profile
            )
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found")

        serializer = AppointmentDoctorNotesSerializer(data=request.data)
        if serializer.is_valid():
            appointment.doctor_notes = serializer.validated_data.get('doctor_notes', '')
            appointment.prescription = serializer.validated_data.get('prescription', '')
            appointment.save()
            
            return Response({
                "message": "Notes updated successfully",
                "appointment": DoctorAppointmentSerializer(appointment).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorCancelAppointmentView(APIView):
    """Doctor cancels an appointment."""
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(
                pk=pk, 
                doctor=request.user.doctor_profile
            )
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found")

        if appointment.status not in ['pending', 'confirmed']:
            return Response(
                {"error": "Only pending or confirmed appointments can be cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AppointmentCancelSerializer(data=request.data)
        if serializer.is_valid():
            reason = serializer.validated_data.get('cancellation_reason', '')
            appointment.cancel(cancelled_by='doctor', reason=reason)
            
            return Response({
                "message": "Appointment cancelled successfully",
                "appointment": DoctorAppointmentSerializer(appointment).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorCompleteAppointmentView(APIView):
    """Doctor marks appointment as completed."""
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(
                pk=pk, 
                doctor=request.user.doctor_profile
            )
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found")

        if appointment.status != 'confirmed':
            return Response(
                {"error": "Only confirmed appointments can be marked as completed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = 'completed'
        appointment.consultation_ended_at = timezone.now()
        appointment.save()
        
        # Update time slot status
        appointment.time_slot.status = 'booked'
        appointment.time_slot.save()

        return Response({
            "message": "Appointment marked as completed",
            "appointment": DoctorAppointmentSerializer(appointment).data
        })


class DoctorStartConsultationView(APIView):
    """Doctor starts the consultation."""
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(
                pk=pk, 
                doctor=request.user.doctor_profile
            )
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found")

        if appointment.status != 'confirmed':
            return Response(
                {"error": "Only confirmed appointments can start consultation"},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.consultation_started_at = timezone.now()
        appointment.save()

        return Response({
            "message": "Consultation started",
            "appointment": DoctorAppointmentSerializer(appointment).data
        })


# =============================================================================
# PAYMENT VIEWS
# =============================================================================

class InitiatePaymentView(APIView):
    """Initiate PayPal payment for an appointment."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk, user=request.user)
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found")

        if appointment.status != 'pending':
            return Response(
                {"error": "Only pending appointments can be paid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        configure_paypal()

        # Calculate amount
        amount = str(appointment.time_slot.effective_fee)
        
        # Create PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/appointment/success?appointment_id={appointment.id}",
                "cancel_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/appointment/cancel?appointment_id={appointment.id}"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"Consultation with Dr. {appointment.doctor.user.get_full_name() or appointment.doctor.user.email}",
                        "sku": str(appointment.appointment_number),
                        "price": amount,
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": amount,
                    "currency": "USD"
                },
                "description": f"Appointment {appointment.appointment_number}"
            }]
        })

        if payment.create():
            # Save payment ID
            appointment.payment_id = payment.id
            appointment.save()

            # Find approval URL
            for link in payment.links:
                if link.rel == "approval_url":
                    return Response({
                        "payment_id": payment.id,
                        "approval_url": str(link.href),
                        "appointment_id": appointment.id
                    })
        
        logger.error(f"PayPal payment creation failed: {payment.error}")
        return Response(
            {"error": "Failed to create payment", "details": payment.error},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ExecutePaymentView(APIView):
    """Execute/confirm PayPal payment."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = AppointmentPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_id = serializer.validated_data['payment_id']
        payer_id = serializer.validated_data['payer_id']

        try:
            appointment = Appointment.objects.get(pk=pk, user=request.user)
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found")

        if appointment.payment_id != payment_id:
            return Response(
                {"error": "Payment ID mismatch"},
                status=status.HTTP_400_BAD_REQUEST
            )

        configure_paypal()

        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # Update appointment
            appointment.confirm_payment(transaction_id=payment.id)
            
            return Response({
                "message": "Payment successful",
                "appointment": AppointmentDetailSerializer(appointment).data
            })
        
        logger.error(f"PayPal payment execution failed: {payment.error}")
        return Response(
            {"error": "Payment execution failed", "details": payment.error},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ConfirmAppointmentView(APIView):
    """Manually confirm appointment (for testing/admin)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk, user=request.user)
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found")

        serializer = AppointmentConfirmSerializer(data=request.data)
        if serializer.is_valid():
            transaction_id = serializer.validated_data.get('transaction_id', f'manual_{timezone.now().timestamp()}')
            appointment.confirm_payment(transaction_id=transaction_id)
            
            return Response({
                "message": "Appointment confirmed",
                "appointment": AppointmentDetailSerializer(appointment).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# REVIEW VIEWS
# =============================================================================

class ReviewCreateView(generics.CreateAPIView):
    """Create a review for a completed appointment."""
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewListView(generics.ListAPIView):
    """List reviews for a doctor."""
    permission_classes = [AllowAny]
    serializer_class = ReviewListSerializer

    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        return Review.objects.filter(doctor_id=doctor_id).order_by('-created_at')


class MyReviewsView(generics.ListAPIView):
    """List logged-in user's reviews."""
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewListSerializer

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user).order_by('-created_at')


class DoctorReviewResponseView(APIView):
    """Doctor responds to a review."""
    permission_classes = [IsAuthenticated, IsDoctor]

    def patch(self, request, pk):
        try:
            review = Review.objects.get(pk=pk, doctor=request.user.doctor_profile)
        except Review.DoesNotExist:
            raise NotFound("Review not found")

        serializer = ReviewDoctorResponseSerializer(data=request.data)
        if serializer.is_valid():
            review.doctor_response = serializer.validated_data['doctor_response']
            review.save()
            
            return Response({
                "message": "Response added",
                "review": ReviewListSerializer(review).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# FAVORITE DOCTOR VIEWS
# =============================================================================

class FavoriteDoctorListView(generics.ListAPIView):
    """List user's favorite doctors."""
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteDoctorSerializer

    def get_queryset(self):
        return FavoriteDoctor.objects.filter(user=self.request.user)


class FavoriteDoctorToggleView(APIView):
    """Add or remove a doctor from favorites."""
    permission_classes = [IsAuthenticated]

    def post(self, request, doctor_id):
        from apps.accounts.models import DoctorProfile
        
        try:
            doctor = DoctorProfile.objects.get(id=doctor_id)
        except DoctorProfile.DoesNotExist:
            raise NotFound("Doctor not found")

        favorite, created = FavoriteDoctor.objects.get_or_create(
            user=request.user,
            doctor=doctor
        )

        if not created:
            favorite.delete()
            return Response({
                "message": "Doctor removed from favorites",
                "is_favorite": False
            })
        
        return Response({
            "message": "Doctor added to favorites",
            "is_favorite": True
        }, status=status.HTTP_201_CREATED)


class CheckFavoriteView(APIView):
    """Check if a doctor is in favorites."""
    permission_classes = [IsAuthenticated]

    def get(self, request, doctor_id):
        is_favorite = FavoriteDoctor.objects.filter(
            user=request.user,
            doctor_id=doctor_id
        ).exists()
        
        return Response({"is_favorite": is_favorite})


# =============================================================================
# APPOINTMENT STATISTICS
# =============================================================================

class AppointmentStatsView(APIView):
    """Get appointment statistics for logged-in user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.user_type == 'doctor':
            appointments = Appointment.objects.filter(doctor=user.doctor_profile)
        else:
            appointments = Appointment.objects.filter(user=user)
        
        stats = {
            "total": appointments.count(),
            "pending": appointments.filter(status='pending').count(),
            "confirmed": appointments.filter(status='confirmed').count(),
            "completed": appointments.filter(status='completed').count(),
            "cancelled": appointments.filter(status='cancelled').count(),
        }
        
        return Response(stats)
