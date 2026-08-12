import os
import secrets
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"]
CALENDAR_ID = os.environ["GOOGLE_CALENDAR_ID"]
CLINIC_TIMEZONE = os.environ.get("CLINIC_TIMEZONE", "America/New_York")
TZ = ZoneInfo(CLINIC_TIMEZONE)

BUSINESS_HOURS = {
    0: (9, 18), 1: (9, 18), 2: (9, 18), 3: (9, 18), 4: (9, 18),
    5: (9, 13),
    6: None,
}


def _localize(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ)
    return dt


def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


def is_within_business_hours(dt: datetime) -> bool:
    hours = BUSINESS_HOURS.get(dt.weekday())
    if hours is None:
        return False
    open_hour, close_hour = hours
    return open_hour <= dt.hour < close_hour


def check_availability(start_dt: datetime, duration_minutes: int = 30) -> bool:
    start_dt = _localize(start_dt)
    if not is_within_business_hours(start_dt):
        return False

    end_dt = start_dt + timedelta(minutes=duration_minutes)
    service = get_calendar_service()

    body = {
        "timeMin": start_dt.isoformat(),
        "timeMax": end_dt.isoformat(),
        "timeZone": CLINIC_TIMEZONE,
        "items": [{"id": CALENDAR_ID}],
    }
    result = service.freebusy().query(body=body).execute()
    busy_slots = result["calendars"][CALENDAR_ID]["busy"]
    return len(busy_slots) == 0


def find_next_available_slot(preferred_dt: datetime, duration_minutes: int = 30, max_days_ahead: int = 7) -> datetime | None:
    candidate = _localize(preferred_dt)
    limit = candidate + timedelta(days=max_days_ahead)

    while candidate < limit:
        if check_availability(candidate, duration_minutes):
            return candidate
        candidate += timedelta(minutes=30)
    return None


def generate_booking_id() -> str:
    """Short, speakable booking ID — e.g. BP482913. Digits only after the
    prefix so it's easy to say and hear correctly over a phone call."""
    digits = "".join(secrets.choice("0123456789") for _ in range(6))
    return f"BP{digits}"


def create_appointment(
    start_dt: datetime,
    patient_name: str,
    reason: str,
    duration_minutes: int = 30,
) -> dict:
    """Creates the event and returns {booking_id, event_id, link}."""
    booking_id = generate_booking_id()
    start_dt = _localize(start_dt)
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    service = get_calendar_service()

    event = {
        "summary": f"{patient_name} — {reason} [{booking_id}]",
        "description": f"Booked via voice receptionist.\nReason: {reason}\nBooking ID: {booking_id}",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": CLINIC_TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": CLINIC_TIMEZONE},
        "extendedProperties": {
            "private": {
                "booking_id": booking_id,
                "patient_name": patient_name,
                "reason": reason,
            }
        },
    }

    created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return {
        "booking_id": booking_id,
        "event_id": created["id"],
        "link": created.get("htmlLink", ""),
    }


def find_appointment_by_booking_id(booking_id: str) -> dict | None:
    """Exact-match lookup via Calendar's private extended property — no
    text-matching ambiguity, works even with duplicate patient names."""
    service = get_calendar_service()
    now = datetime.now(TZ)

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now.isoformat(),
        privateExtendedProperty=f"booking_id={booking_id}",
        singleEvents=True,
        orderBy="startTime",
        maxResults=1,
    ).execute()

    items = events_result.get("items", [])
    if not items:
        return None

    event = items[0]
    props = event.get("extendedProperties", {}).get("private", {})
    start = event["start"].get("dateTime", event["start"].get("date"))

    return {
        "event_id": event["id"],
        "booking_id": booking_id,
        "patient_name": props.get("patient_name", ""),
        "reason": props.get("reason", ""),
        "start": start,
    }


def cancel_appointment(event_id: str) -> None:
    service = get_calendar_service()
    service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()


def reschedule_appointment(event_id: str, new_start_dt: datetime, duration_minutes: int = 30) -> str:
    new_start_dt = _localize(new_start_dt)
    new_end_dt = new_start_dt + timedelta(minutes=duration_minutes)
    service = get_calendar_service()

    event = service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
    event["start"] = {"dateTime": new_start_dt.isoformat(), "timeZone": CLINIC_TIMEZONE}
    event["end"] = {"dateTime": new_end_dt.isoformat(), "timeZone": CLINIC_TIMEZONE}

    updated = service.events().update(calendarId=CALENDAR_ID, eventId=event_id, body=event).execute()
    return updated.get("htmlLink", "")