# scripts/test_email_service.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta
from app.config import TEST_PATIENT_EMAILS
from app.services.email_service import (
    notify_clinic_new_booking,
    send_patient_booking_confirmation,
)

if __name__ == "__main__":
    if not TEST_PATIENT_EMAILS:
        print("❌ No TEST_PATIENT_EMAIL_1 / TEST_PATIENT_EMAIL_2 set in .env — cannot test.")
        sys.exit(1)

    test_email = TEST_PATIENT_EMAILS[0]
    test_time = datetime.now() + timedelta(days=2)

    print(f"Testing Resend (clinic notification)...")
    notify_clinic_new_booking(
        booking_id="BP999999",
        patient_name="Test Email Patient",
        patient_age=30,
        patient_email=test_email,
        reason="Email service test",
        scheduled_time=test_time,
    )

    print(f"\nTesting Gmail SMTP (patient confirmation) to whitelisted address {test_email}...")
    send_patient_booking_confirmation(
        patient_email=test_email,
        patient_name="Test Email Patient",
        booking_id="BP999999",
        scheduled_time=test_time,
        reason="Email service test",
    )

    print(f"\nTesting Gmail SMTP whitelist guard (should SKIP, not send)...")
    send_patient_booking_confirmation(
        patient_email="aqua85878@gmail.com",
        patient_name="Should Not Receive This",
        booking_id="BP000000",
        scheduled_time=test_time,
        reason="Whitelist guard test",
    )

    print("\n✅ Script finished. Check the console output above and your inboxes.")