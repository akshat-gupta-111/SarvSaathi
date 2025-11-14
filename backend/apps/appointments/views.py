from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.conf import settings
from .serializers import PatientAppointmentListSerializer
from decimal import Decimal
from .serializers import DoctorScheduleSerializer
from .permissions import IsDoctor
from django.utils import timezone



# Import our models
from .models import TimeSlot, Appointment
from apps.accounts.models import Patient

# Import all our serializers
from .serializers import (
    TimeSlotCreateSerializer,
    TimeSlotListSerializer,
    AppointmentCreateSerializer,
    AppointmentInitiateSerializer,
    AppointmentExecuteSerializer,
    AppointmentDetailSerializer
)
# Import our permission
from .permissions import IsDoctor

# --- PayPal Imports ---
import paypalrestsdk
import logging

paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# --- Configure PayPal SDK ---
# This runs once when the file is loaded.
try:
    paypalrestsdk.configure({
        "mode": settings.PAYPAL_MODE,  # "sandbox" or "live"
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET
    })
    logging.info("PayPal SDK configured successfully.")
except Exception as e:
    logging.error(f"Failed to configure PayPal SDK: {e}")


# --- View 1: For Doctors (CREATE and LIST their own slots) ---
# (This is Phase 1, but I've fixed it to use the correct serializers)

class DoctorTimeSlotListCreateView(generics.ListCreateAPIView):
    """
    API View for authenticated DOCTORS to:
    - GET: List all of their own time slots.
    - POST: Create a new time slot for themselves.
    """
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_serializer_class(self):
        """
        Use the correct serializer based on the HTTP method.
        POST (Create) -> TimeSlotCreateSerializer
        GET (List)    -> TimeSlotListSerializer
        """
        if self.request.method == 'POST':
            return TimeSlotCreateSerializer
        return TimeSlotListSerializer

    def get_queryset(self):
        """
        This view should only return time slots for the
        currently logged-in doctor.
        """
        return TimeSlot.objects.filter(doctor=self.request.user.doctor_profile)

    def perform_create(self, serializer):
        """
        When a doctor creates a new slot, automatically assign
        it to their own DoctorProfile.
        """
        serializer.save(doctor=self.request.user.doctor_profile)

# --- View 2: For Patients (LIST available slots for a doctor) ---
# (This is Phase 1, no changes needed)

class PatientTimeSlotListView(generics.ListAPIView):
    """
    API View for ANY user (Patient or public) to:
    - GET: List all *available* and *future* time slots for a
      specific doctor.
    """
    serializer_class = TimeSlotListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        if not doctor_id:
            return TimeSlot.objects.none()
        
        return TimeSlot.objects.filter(
            doctor__id=doctor_id,
            is_available=True,
            start_time__gte=timezone.now()
        )

# --- View 3: For Patients (START a booking - STAGE 1) ---

class AppointmentCreateView(APIView):
    """
    API View for an authenticated PATIENT to create a payment.
    This is STAGE 1 of the booking process.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Validate the incoming data (time_slot_id and patient_id)
        # We pass the request context so the serializer can access the user
        input_serializer = AppointmentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        # The serializer now runs ALL our checks:
        # 1. Is the time slot valid?
        # 2. Is the patient ID valid and does it belong to the user?
        # 3. Is that patient's profile complete?
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Get the validated objects from the serializer's context
        time_slot = input_serializer.context['time_slot']
        patient = input_serializer.context['patient']  # <-- THIS IS THE FIX
        doctor = time_slot.doctor

        # 3. Calculate the amount
        amount_decimal = Decimal(0)
        if time_slot.mode == 'IN_CLINIC':
            amount_decimal = Decimal(settings.BOOKING_TOKEN_AMOUNT_IN_USD)
        else: # 'ONLINE'
            amount_decimal = doctor.consultation_fee
        
        # Format for PayPal
        amount_str = "{:.2f}".format(amount_decimal) 
        currency = "USD" # Set currency to US Dollars

        # 4. Create the local Appointment object
        appointment = Appointment.objects.create(
            patient=patient,  # <-- Use the validated patient
            time_slot=time_slot,
            status='PENDING_PAYMENT',
            payment_status='UNPAID',
            amount_paid=Decimal(0) # Nothing paid yet
        )
        
        # 5. --- ADAPTED FROM YOUR PAYPAL CODE ---
        # Build the PayPal payment object
        payment_data = {
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": settings.PAYMENT_SUCCESS_URL,
                "cancel_url": settings.PAYMENT_CANCEL_URL
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"Appointment with Dr. {doctor.last_name}",
                        "sku": f"APT-{appointment.id}",
                        "price": amount_str,
                        "currency": currency,
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": amount_str,
                    "currency": currency
                },
                "description": f"Booking for {time_slot.start_time.strftime('%Y-%m-%d %I:%M %p')}"
            }]
        }

        try:
            payment = paypalrestsdk.Payment(payment_data)

            if payment.create():
                # 6. Save the PayPal Payment ID to our Appointment
                appointment.payment_order_id = payment.id
                appointment.save()

                # 7. Find and send the approval_url to the frontend
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = str(link.href)
                
                if approval_url:
                    # Use the "receipt" serializer to send the URL back
                    output_serializer = AppointmentInitiateSerializer({"approval_url": approval_url})
                    return Response(output_serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": "Could not get approval URL from PayPal."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            else:
                logging.error(f"PayPal payment.create() error: {payment.error}")
                # If PayPal fails, cancel our local appointment
                appointment.status = 'CANCELLED'
                appointment.save()
                return Response({"error": "PayPal Error", "details": payment.error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logging.error(f"PayPal SDK Exception: {e}")
            return Response({"error": "An error occurred with the payment gateway."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# --- View 4: For Frontend (EXECUTE a payment - STAGE 3) ---

class AppointmentExecuteView(APIView):
    """
    API View for the frontend to confirm a payment.
    This is STAGE 3 of the booking process.
    """
    permission_classes = [AllowAny] # Anyone can hit this, but we validate the data

    def post(self, request, *args, **kwargs):
        # 1. Validate the incoming 'paymentId' and 'PayerID'
        input_serializer = AppointmentExecuteSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_id = input_serializer.validated_data['paymentId']
        payer_id = input_serializer.validated_data['PayerID']

        # 2. --- ADAPTED FROM YOUR PAYPAL CODE ---
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            # 3. Execute the payment
            if payment.execute({"payer_id": payer_id}):
                # 4. Success! Now, update OUR database
                try:
                    # Find our appointment using the saved payment ID
                    appointment = Appointment.objects.get(payment_order_id=payment.id)
                except Appointment.DoesNotExist:
                    logging.error(f"CRITICAL: Payment {payment.id} executed but no matching appointment found.")
                    return Response({"error": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

                # 5. Confirm the booking
                appointment.status = 'CONFIRMED'
                appointment.payment_status = 'PAID'
                
                # Save the amount paid from the transaction
                try:
                    amount_paid = Decimal(payment.transactions[0].amount.total)
                    appointment.amount_paid = amount_paid
                except Exception:
                    pass # Keep default

                appointment.save()

                # 6. Secure the time slot
                appointment.time_slot.is_available = False
                appointment.time_slot.save()
                
                # 7. (This is where you would trigger your email/WhatsApp utilities)
                # send_confirmation_email(appointment.patient.email, ...)

                # Send back the confirmed appointment details
                output_serializer = AppointmentDetailSerializer(appointment)
                return Response(output_serializer.data, status=status.HTTP_200_OK)
            
            else:
                # Payment execution failed
                logging.error(f"PayPal payment.execute() error: {payment.error}")
                return Response({"error": "Payment execution failed", "details": payment.error}, status=status.HTTP_400_BAD_REQUEST)
        
        except paypalrestsdk.ResourceNotFound:
            logging.error(f"PayPal Payment.find() error: Payment {payment_id} not found.")
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logging.error(f"PayPal SDK Exception during execute: {e}")
            return Response({"error": "An error occurred with the payment gateway."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

# --- View 5: For Frontend (CANCEL a payment) ---

class AppointmentCancelView(APIView):
    """
    A simple view to log that a user cancelled.
    The frontend should redirect here from PayPal's cancel_url.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # We don't need to do much here, but we could log this.
        logging.info("A user cancelled a PayPal payment.")
        # In a real app, you'd redirect to a "Your payment was cancelled" page
        return Response({"message": "Payment was cancelled."}, status=status.HTTP_200_OK)


# --- View 6: For Patients (List their own appointments) ---
class PatientAppointmentListView(generics.ListAPIView):
    """
    API View for an authenticated PATIENT to see a list of
    their own 'CONFIRMED' or 'COMPLETED' appointments.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PatientAppointmentListSerializer

    def get_queryset(self):
        """
        This view only returns appointments for the logged-in user.
        """
        # Get the currently logged-in user
        user = self.request.user
        
        # We only want to show appointments that are confirmed or finished.
        # We filter out 'PENDING_PAYMENT' and 'CANCELLED' ones.
        valid_statuses = ['CONFIRMED', 'COMPLETED']
        
        # Find all patients (family members) linked to this user's account
        patient_profiles = user.patients.all()
        
        # Return all appointments for any of those patient profiles
        return Appointment.objects.filter(
            patient__in=patient_profiles,
            status__in=valid_statuses
        ).order_by('time_slot__start_time') # Show upcoming ones first
    

# --- View 7: For Doctors (List their own schedule) ---
class DoctorScheduleListView(generics.ListAPIView):
    """
    API View for an authenticated DOCTOR to see a list of
    their own upcoming 'CONFIRMED' appointments.
    """
    permission_classes = [IsDoctor, IsAuthenticated]
    serializer_class = DoctorScheduleSerializer

    def get_queryset(self):
        """
        This view only returns appointments for the logged-in doctor.
        """
        # Get the currently logged-in doctor's profile
        doctor_profile = self.request.user.doctor_profile
        
        # We only want to show appointments that are
        # confirmed and in the future.
        return Appointment.objects.filter(
            time_slot__doctor=doctor_profile,
            status='CONFIRMED',
            time_slot__start_time__gte=timezone.now() # Only show future appointments
        ).order_by('time_slot__start_time') # Show upcoming ones first