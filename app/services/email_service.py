import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import resend

from app.config import (
    RESEND_API_KEY,
    CLINIC_NOTIFICATION_EMAILS,
    GMAIL_SMTP_USER,
    GMAIL_SMTP_APP_PASSWORD,
    TEST_PATIENT_EMAILS,
)

resend.api_key = RESEND_API_KEY


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%A, %B %d, %Y at %I:%M %p")


# ---------------------------------------------------------------------------
# Resend — internal clinic staff notification
# ---------------------------------------------------------------------------

def notify_clinic_new_booking(booking_id: str, patient_name: str, patient_age,
                                patient_email: str, reason: str, scheduled_time: datetime) -> None:
    if not CLINIC_NOTIFICATION_EMAILS:
        print("[email] No clinic notification emails configured, skipping.")
        return

    html = f"""
    <h2>New Appointment Booked</h2>
    <p><strong>Booking ID:</strong> {booking_id}</p>
    <p><strong>Patient:</strong> {patient_name} (age {patient_age})</p>
    <p><strong>Email:</strong> {patient_email}</p>
    <p><strong>Reason:</strong> {reason}</p>
    <p><strong>Scheduled:</strong> {_format_dt(scheduled_time)}</p>
    <p><em>Booked via the voice AI receptionist.</em></p>
    """

    _send_via_resend(f"New Booking — {patient_name} — {booking_id}", html)


def notify_clinic_reschedule(booking_id: str, patient_name: str, old_time, new_time: datetime) -> None:
    if not CLINIC_NOTIFICATION_EMAILS:
        print("[email] No clinic notification emails configured, skipping.")
        return

    html = f"""
    <h2>Appointment Rescheduled</h2>
    <p><strong>Booking ID:</strong> {booking_id}</p>
    <p><strong>Patient:</strong> {patient_name}</p>
    <p><strong>Old time:</strong> {_format_dt(old_time) if old_time else 'unknown'}</p>
    <p><strong>New time:</strong> {_format_dt(new_time)}</p>
    """

    _send_via_resend(f"Rescheduled — {patient_name} — {booking_id}", html)


def notify_clinic_cancellation(booking_id: str, patient_name: str, scheduled_time) -> None:
    if not CLINIC_NOTIFICATION_EMAILS:
        print("[email] No clinic notification emails configured, skipping.")
        return

    html = f"""
    <h2>Appointment Cancelled</h2>
    <p><strong>Booking ID:</strong> {booking_id}</p>
    <p><strong>Patient:</strong> {patient_name}</p>
    <p><strong>Was scheduled:</strong> {_format_dt(scheduled_time) if scheduled_time else 'unknown'}</p>
    """

    _send_via_resend(f"Cancelled — {patient_name} — {booking_id}", html)


def _send_via_resend(subject: str, html: str) -> None:
    try:
        resend.Emails.send({
            "from": "BrightPath Clinic <onboarding@resend.dev>",
            "to": CLINIC_NOTIFICATION_EMAILS,
            "subject": subject,
            "html": html,
        })
        print(f"[email] Clinic notification sent: {subject}")
    except Exception as e:
        print(f"[email] Failed to send clinic notification: {e}")


# ---------------------------------------------------------------------------
# Gmail SMTP — patient-facing confirmation (whitelisted test emails only)
# ---------------------------------------------------------------------------

def _send_via_gmail(to_email: str, subject: str, body_html: str) -> None:
    if not GMAIL_SMTP_USER or not GMAIL_SMTP_APP_PASSWORD:
        print("[email] Gmail SMTP not configured, skipping patient email.")
        return

    if to_email.lower() not in TEST_PATIENT_EMAILS:
        print(f"[email] Skipping patient email to {to_email} — not in test whitelist. "
              f"Would have sent: '{subject}'")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_SMTP_USER, GMAIL_SMTP_APP_PASSWORD)
            server.sendmail(GMAIL_SMTP_USER, to_email, msg.as_string())
        print(f"[email] Patient confirmation sent to {to_email}")
    except Exception as e:
        print(f"[email] Failed to send patient confirmation: {e}")


def send_patient_booking_confirmation(patient_email: str, patient_name: str,
                                        booking_id: str, scheduled_time: datetime, reason: str) -> None:
    html = f"""
    <h2>Your appointment is confirmed</h2>
    <p>Hi {patient_name},</p>
    <p>Your appointment at BrightPath Clinic is confirmed for:</p>
    <p><strong>{_format_dt(scheduled_time)}</strong></p>
    <p><strong>Reason:</strong> {reason}</p>
    <p><strong>Booking ID:</strong> {booking_id}</p>
    <p>Please save this ID — you'll need it if you want to reschedule or cancel later.</p>
    <p>See you then!<br>BrightPath Clinic</p>
    """
    _send_via_gmail(patient_email, "Your BrightPath Clinic appointment is confirmed", html)


def send_patient_reschedule_confirmation(patient_email: str, patient_name: str,
                                           booking_id: str, new_time: datetime) -> None:
    html = f"""
    <h2>Your appointment has been rescheduled</h2>
    <p>Hi {patient_name},</p>
    <p>Your appointment has been moved to:</p>
    <p><strong>{_format_dt(new_time)}</strong></p>
    <p><strong>Booking ID:</strong> {booking_id}</p>
    <p>See you then!<br>BrightPath Clinic</p>
    """
    _send_via_gmail(patient_email, "Your BrightPath Clinic appointment was rescheduled", html)


def send_patient_cancellation_confirmation(patient_email: str, patient_name: str, booking_id: str) -> None:
    html = f"""
    <h2>Your appointment has been cancelled</h2>
    <p>Hi {patient_name},</p>
    <p>Your appointment (booking ID {booking_id}) has been cancelled as requested.</p>
    <p>If this was a mistake, please call us back to rebook.</p>
    <p>BrightPath Clinic</p>
    """
    _send_via_gmail(patient_email, "Your BrightPath Clinic appointment was cancelled", html)