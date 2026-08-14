"""
Synchronous wrappers around the email MCP tools, for use in LangGraph node
functions. Mirrors the old app.services.email_service function signatures.
"""
from datetime import datetime
from app.mcp.client import get_email_tools, unwrap_tool_result
from app.mcp.sync_bridge import run_async

_tools_cache = None


def _get_tools():
    global _tools_cache
    if _tools_cache is None:
        _tools_cache = run_async(get_email_tools())
    return _tools_cache


def notify_clinic_new_booking(booking_id: str, patient_name: str, patient_age,
                                patient_email: str, reason: str, scheduled_time: datetime) -> None:
    tools = _get_tools()
    run_async(tools["notify_clinic_new_booking"].ainvoke({
        "booking_id": booking_id,
        "patient_name": patient_name,
        "patient_age": patient_age,
        "patient_email": patient_email,
        "reason": reason,
        "iso_scheduled_time": scheduled_time.isoformat(),
    }))


def notify_clinic_reschedule(booking_id: str, patient_name: str, old_time, new_time: datetime) -> None:
    tools = _get_tools()
    run_async(tools["notify_clinic_reschedule"].ainvoke({
        "booking_id": booking_id,
        "patient_name": patient_name,
        "iso_old_time": old_time.isoformat() if old_time else None,
        "iso_new_time": new_time.isoformat(),
    }))


def notify_clinic_cancellation(booking_id: str, patient_name: str, scheduled_time) -> None:
    tools = _get_tools()
    run_async(tools["notify_clinic_cancellation"].ainvoke({
        "booking_id": booking_id,
        "patient_name": patient_name,
        "iso_scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
    }))


def send_patient_booking_confirmation(patient_email: str, patient_name: str,
                                        booking_id: str, scheduled_time: datetime, reason: str) -> None:
    tools = _get_tools()
    run_async(tools["send_patient_booking_confirmation"].ainvoke({
        "patient_email": patient_email,
        "patient_name": patient_name,
        "booking_id": booking_id,
        "iso_scheduled_time": scheduled_time.isoformat(),
        "reason": reason,
    }))


def send_patient_reschedule_confirmation(patient_email: str, patient_name: str,
                                           booking_id: str, new_time: datetime) -> None:
    tools = _get_tools()
    run_async(tools["send_patient_reschedule_confirmation"].ainvoke({
        "patient_email": patient_email,
        "patient_name": patient_name,
        "booking_id": booking_id,
        "iso_new_time": new_time.isoformat(),
    }))


def send_patient_cancellation_confirmation(patient_email: str, patient_name: str, booking_id: str) -> None:
    tools = _get_tools()
    run_async(tools["send_patient_cancellation_confirmation"].ainvoke({
        "patient_email": patient_email,
        "patient_name": patient_name,
        "booking_id": booking_id,
    }))