import os
import logging
from twilio.rest import Client
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- A. SMS NOTIFICATION (from your notify.txt/Twilio script) ---

def send_emergency_sms(phone_number, message_body):
    """
    Sends an SMS using Twilio credentials from environment.
    """
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_FROM_NUMBER")  # Fixed: Match .env variable name

    if not (sid and token and from_num):
        logging.error("Twilio SMS credentials (SID, TOKEN, FROM_NUMBER) not set. Cannot send SMS.")
        logging.error(f"Debug - SID: {bool(sid)}, TOKEN: {bool(token)}, FROM_NUMBER: {bool(from_num)}")
        return False

    try:
        client = Client(sid, token)
        message = client.messages.create(
            body=message_body, 
            from_=from_num, 
            to=phone_number # e.g., "+919876543210"
        )
        logging.info(f"Emergency SMS sent to {phone_number} (SID: {message.sid})")
        return True
    except Exception as e:
        # This will catch the "21408" error
        logging.error(f"Failed to send emergency SMS: {e}")
        return False

# --- B. EMAIL NOTIFICATION (from your notify.txt) ---

def send_emergency_email(recipient_email, message_body):
    """
    Sends a simple text email via Gmail.
    """
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_APP_PASSWORD")
    
    if not (sender_email and sender_password):
        logging.error("Gmail credentials (SENDER_EMAIL, SENDER_APP_PASSWORD) not set. Cannot send email.")
        return False

    msg = EmailMessage()
    msg["Subject"] = "EMERGENCY ALERT"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content(message_body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        logging.info(f"Emergency Email sent to {recipient_email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send emergency email: {e}")
        return False

# --- C. WHATSAPP NOTIFICATION (FIXED - from your Twilio script) ---

def send_emergency_whatsapp(phone_number, message_body):
    """
    Sends a WhatsApp message using Twilio credentials from environment.
    """
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_WHATSAPP_NUMBER") # This now has "whatsapp:+1..."

    if not (sid and token and from_num):
        logging.error("Twilio WhatsApp credentials (SID, TOKEN, WHATSAPP_NUMBER) not set. Cannot send WhatsApp.")
        return False

    # Twilio requires "whatsapp:" prefix for the recipient number
    to_num = f"whatsapp:{phone_number}" 

    try:
        client = Client(sid, token)
        message = client.messages.create(
            body=message_body,
            from_=from_num,
            to=to_num
        )
        logging.info(f"Emergency WhatsApp sent to {to_num} (SID: {message.sid})")
        return True
    except Exception as e:
        # This will catch the "unverified number" error
        logging.error(f"Failed to send emergency WhatsApp: {e}")
        return False
    
def _get_twilio_client():
    """Helper to get Twilio client or log error."""
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not (sid and token):
        logging.error("Twilio credentials (SID, TOKEN) not set.")
        return None
    return Client(sid, token)

def _get_gmail_smtp():
    """Helper to get a logged-in Gmail SMTP client."""
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_APP_PASSWORD")
    if not (sender_email and sender_password):
        logging.error("Gmail credentials not set.")
        return None
    
    context = ssl.create_default_context()
    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
    smtp.login(sender_email, sender_password)
    return smtp, sender_email

# --- 1. NOTIFICATIONS FOR THE PATIENT ---

def send_confirmation_email_to_patient(patient, appointment):
    """
    Sends a detailed confirmation email/bill to the patient.
    """
    try:
        smtp, sender_email = _get_gmail_smtp()
        if not smtp:
            return

        subject = f"Appointment Confirmed: {appointment.time_slot.start_time.strftime('%Y-%m-%d %I:%M %p')}"
        body = (
            f"Hello {patient.first_name},\n\n"
            f"Your appointment with Dr. {appointment.time_slot.doctor.user_full_name} is confirmed.\n\n"
            f"--- Details ---\n"
            f"Date: {appointment.time_slot.start_time.strftime('%A, %B %d, %Y')}\n"
            f"Time: {appointment.time_slot.start_time.strftime('%I:%M %p')}\n"
            f"Mode: {appointment.time_slot.get_mode_display()}\n\n"
            f"--- Billing ---\n"
            f"Amount Paid: {appointment.amount_paid} INR\n"
            f"Status: {appointment.get_payment_status_display()}\n"
            f"Payment ID: {appointment.payment_order_id}\n\n"
            f"Thank you,\n"
            f"The SarvSaathi Team"
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = patient.email
        msg.set_content(body)
        
        with smtp:
            smtp.send_message(msg)
        logging.info(f"Confirmation email sent to patient {patient.email}")
    except Exception as e:
        logging.error(f"Failed to send patient confirmation email: {e}")

def send_confirmation_sms_to_patient(patient, appointment):
    """
    Sends a short confirmation SMS to the patient.
    """
    try:
        client = _get_twilio_client()
        from_num = os.getenv("TWILIO_SMS_NUMBER")
        if not (client and from_num):
            return

        body = (
            f"SarvSaathi: Your appointment with Dr. {appointment.time_slot.doctor.last_name} on "
            f"{appointment.time_slot.start_time.strftime('%b %d at %I:%M %p')} is CONFIRMED. "
            f"Amount Paid: {appointment.amount_paid} INR."
        )
        
        client.messages.create(body=body, from_=from_num, to=patient.phone_number)
        logging.info(f"Confirmation SMS sent to patient {patient.phone_number}")
    except Exception as e:
        logging.error(f"Failed to send patient confirmation SMS: {e}")


# --- 2. NOTIFICATIONS FOR THE DOCTOR ---

def send_new_booking_alert_to_doctor(doctor, patient, appointment):
    """
    Sends an alert to the Doctor about the new booking.
    (We will use Email for now, but can add SMS/WhatsApp)
    """
    try:
        smtp, sender_email = _get_gmail_smtp()
        if not smtp:
            return

        subject = f"New Booking: {patient.first_name} {patient.last_name} on {appointment.time_slot.start_time.strftime('%b %d')}"
        body = (
            f"Hello Dr. {doctor.last_name},\n\n"
            f"You have a new confirmed appointment:\n\n"
            f"Patient: {patient.first_name} {patient.last_name}\n"
            f"Patient Phone: {patient.phone_number}\n"
            f"Date: {appointment.time_slot.start_time.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
            f"Mode: {appointment.time_slot.get_mode_display()}\n"
            f"Patient Notes: {appointment.patient_notes}\n"
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = doctor.user.email
        msg.set_content(body)
        
        with smtp:
            smtp.send_message(msg)
        logging.info(f"New booking alert email sent to doctor {doctor.user.email}")
    except Exception as e:
        logging.error(f"Failed to send doctor alert email: {e}")

