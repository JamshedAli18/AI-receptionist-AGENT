"""
MCP server exposing email operations as tools. Wraps the existing,
already-tested app/services/email_service.py functions.

Run standalone for testing: uv run python -m app.mcp_servers.email_server
"""
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from app.services.email_service import (
    notify_clinic_new_booking as _notify_clinic_new_booking,
    notify_clinic_reschedule as _notify_clinic_reschedule,
    notify_clinic_cancellation as _notify_clinic_cancellation,
    send_patient_booking_confirmation as _send_patient_booking_confirmation,
    send_patient_reschedule_confirmation as _send_patient_reschedule_confirmation,
    send_patient_cancellation_confirmation as _send_patient_cancellation_confirmation,
)

mcp = FastMCP("email")


@mcp.tool()
def notify_clinic_new_booking(booking_id: str, patient_name: str, patient_age: int,
                                patient_email: str, reason: str, iso_scheduled_time: str) -> dict:
    """Send an internal notification to clinic staff about a new booking (via Resend)."""
    dt = datetime.fromisoformat(iso_scheduled_time)
    _notify_clinic_new_booking(booking_id, patient_name, patient_age, patient_email, reason, dt)
    return {"status": "sent"}


@mcp.tool()
def notify_clinic_reschedule(booking_id: str, patient_name: str,
                               iso_old_time: str | None, iso_new_time: str) -> dict:
    """Send an internal notification to clinic staff about a rescheduled appointment (via Resend)."""
    old_dt = datetime.fromisoformat(iso_old_time) if iso_old_time else None
    new_dt = datetime.fromisoformat(iso_new_time)
    _notify_clinic_reschedule(booking_id, patient_name, old_dt, new_dt)
    return {"status": "sent"}


@mcp.tool()
def notify_clinic_cancellation(booking_id: str, patient_name: str, iso_scheduled_time: str | None) -> dict:
    """Send an internal notification to clinic staff about a cancelled appointment (via Resend)."""
    dt = datetime.fromisoformat(iso_scheduled_time) if iso_scheduled_time else None
    _notify_clinic_cancellation(booking_id, patient_name, dt)
    return {"status": "sent"}


@mcp.tool()
def send_patient_booking_confirmation(patient_email: str, patient_name: str,
                                        booking_id: str, iso_scheduled_time: str, reason: str) -> dict:
    """Send a booking confirmation email to the patient (via Gmail SMTP, whitelisted addresses only)."""
    dt = datetime.fromisoformat(iso_scheduled_time)
    _send_patient_booking_confirmation(patient_email, patient_name, booking_id, dt, reason)
    return {"status": "sent"}


@mcp.tool()
def send_patient_reschedule_confirmation(patient_email: str, patient_name: str,
                                           booking_id: str, iso_new_time: str) -> dict:
    """Send a reschedule confirmation email to the patient (via Gmail SMTP, whitelisted addresses only)."""
    dt = datetime.fromisoformat(iso_new_time)
    _send_patient_reschedule_confirmation(patient_email, patient_name, booking_id, dt)
    return {"status": "sent"}


@mcp.tool()
def send_patient_cancellation_confirmation(patient_email: str, patient_name: str, booking_id: str) -> dict:
    """Send a cancellation confirmation email to the patient (via Gmail SMTP, whitelisted addresses only)."""
    _send_patient_cancellation_confirmation(patient_email, patient_name, booking_id)
    return {"status": "sent"}


if __name__ == "__main__":
    mcp.run(transport="stdio")