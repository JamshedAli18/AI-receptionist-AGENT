"""
MCP server exposing calendar operations as tools. Wraps the existing,
already-tested app/services/calendar_service.py functions — no business
logic changes, just a different transport (MCP stdio) for the graph to
reach them through instead of a direct Python import.

Run standalone for testing: uv run python -m app.mcp_servers.calendar_server
Normally this is launched as a subprocess by the MCP client (see app/mcp/client.py).
"""
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from app.services.calendar_service import (
    check_availability as _check_availability,
    is_within_business_hours as _is_within_business_hours,
    create_appointment as _create_appointment,
    find_appointment_by_booking_id as _find_appointment_by_booking_id,
    cancel_appointment as _cancel_appointment,
    reschedule_appointment as _reschedule_appointment,
)

mcp = FastMCP("calendar")


@mcp.tool()
def check_availability(iso_datetime: str) -> dict:
    """
    Check if a specific date/time slot is available for booking.
    iso_datetime: ISO 8601 datetime string, e.g. '2026-08-20T14:00:00'
    Returns: {"available": bool, "within_business_hours": bool}
    """
    dt = datetime.fromisoformat(iso_datetime)
    within_hours = _is_within_business_hours(dt)
    if not within_hours:
        return {"available": False, "within_business_hours": False}
    available = _check_availability(dt)
    return {"available": available, "within_business_hours": True}


@mcp.tool()
def create_appointment(iso_datetime: str, patient_name: str, patient_email: str, reason: str) -> dict:
    """
    Create a new appointment on the calendar.
    iso_datetime: ISO 8601 datetime string for the appointment start time.
    Returns: {"booking_id": str, "event_id": str, "link": str}
    """
    dt = datetime.fromisoformat(iso_datetime)
    result = _create_appointment(
        start_dt=dt,
        patient_name=patient_name,
        patient_email=patient_email,
        reason=reason,
    )
    return result


@mcp.tool()
def find_appointment_by_booking_id(booking_id: str) -> dict | None:
    """
    Look up an existing appointment by its booking ID (format: BP followed by 6 digits).
    Returns the appointment details, or null if not found.
    """
    return _find_appointment_by_booking_id(booking_id)


@mcp.tool()
def cancel_appointment(event_id: str) -> dict:
    """Cancel/delete an appointment by its calendar event ID."""
    _cancel_appointment(event_id)
    return {"status": "cancelled"}


@mcp.tool()
def reschedule_appointment(event_id: str, new_iso_datetime: str) -> dict:
    """
    Move an existing appointment to a new date/time.
    new_iso_datetime: ISO 8601 datetime string for the new start time.
    """
    dt = datetime.fromisoformat(new_iso_datetime)
    link = _reschedule_appointment(event_id, dt)
    return {"status": "rescheduled", "link": link}


if __name__ == "__main__":
    mcp.run(transport="stdio")