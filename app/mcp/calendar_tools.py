"""
Synchronous wrappers around the calendar MCP tools, for use in LangGraph
node functions. Each function here mirrors the old direct
app.services.calendar_service function signatures, so call sites in
booking_node.py / reschedule_cancel_node.py barely change.
"""
from datetime import datetime
from app.mcp.client import get_calendar_tools, unwrap_tool_result
from app.mcp.sync_bridge import run_async

_tools_cache = None


def _get_tools():
    global _tools_cache
    if _tools_cache is None:
        _tools_cache = run_async(get_calendar_tools())
    return _tools_cache


def check_availability(dt: datetime) -> bool:
    tools = _get_tools()
    raw = run_async(tools["check_availability"].ainvoke({"iso_datetime": dt.isoformat()}))
    result = unwrap_tool_result(raw)
    return bool(result and result.get("available"))


def is_within_business_hours(dt: datetime) -> bool:
    tools = _get_tools()
    raw = run_async(tools["check_availability"].ainvoke({"iso_datetime": dt.isoformat()}))
    result = unwrap_tool_result(raw)
    return bool(result and result.get("within_business_hours"))


def create_appointment(start_dt: datetime, patient_name: str, patient_email: str, reason: str) -> dict:
    tools = _get_tools()
    raw = run_async(tools["create_appointment"].ainvoke({
        "iso_datetime": start_dt.isoformat(),
        "patient_name": patient_name,
        "patient_email": patient_email,
        "reason": reason,
    }))
    return unwrap_tool_result(raw)


def find_appointment_by_booking_id(booking_id: str) -> dict | None:
    tools = _get_tools()
    raw = run_async(tools["find_appointment_by_booking_id"].ainvoke({"booking_id": booking_id}))
    return unwrap_tool_result(raw)


def cancel_appointment(event_id: str) -> None:
    tools = _get_tools()
    run_async(tools["cancel_appointment"].ainvoke({"event_id": event_id}))


def reschedule_appointment(event_id: str, new_start_dt: datetime) -> None:
    tools = _get_tools()
    run_async(tools["reschedule_appointment"].ainvoke({
        "event_id": event_id,
        "new_iso_datetime": new_start_dt.isoformat(),
    }))