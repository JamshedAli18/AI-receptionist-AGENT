import os
import secrets
import time
import ssl
import socket
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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


def _execute_with_retry(request, max_retries=3, base_wait=3):
    last_exc = None
    for attempt in range(max_retries):
        try:
            return request.execute()
        except (TimeoutError, ssl.SSLError, socket.timeout, ConnectionError) as e:
            last_exc = e
            wait = base_wait * (attempt + 1)
            print(f"[calendar] network error, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504):
                last_exc = e
                wait = base_wait * (attempt + 1)
                print(f"[calendar] server error {e.resp.status}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise last_exc


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
    result = _execute_with_retry(service.freebusy().query(body=body))
    busy_slots = result["calendars"][CALENDAR_ID]["busy"]
    return len(busy_slots) == 0


def generate_booking_id() -> str:
    digits = "".join(secrets.choice("0123456789") for _ in range(6))
    return f"BP{digits}"


def create_appointment(
    start_dt: datetime,
    patient_name: str,
    patient_email: str,
    reason: str,
    duration_minutes: int = 30,
) -> dict:
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
                "patient_email": patient_email,
                "reason": reason,
            }
        },
    }

    created = _execute_with_retry(service.events().insert(calendarId=CALENDAR_ID, body=event))
    return {
        "booking_id": booking_id,
        "event_id": created["id"],
        "link": created.get("htmlLink", ""),
    }


def find_appointment_by_booking_id(booking_id: str) -> dict | None:
    service = get_calendar_service()
    now = datetime.now(TZ)

    events_result = _execute_with_retry(service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now.isoformat(),
        privateExtendedProperty=f"booking_id={booking_id}",
        singleEvents=True,
        orderBy="startTime",
        maxResults=1,
    ))

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
        "patient_email": props.get("patient_email", ""),
        "reason": props.get("reason", ""),
        "start": start,
    }


def cancel_appointment(event_id: str) -> None:
    service = get_calendar_service()
    _execute_with_retry(service.events().delete(calendarId=CALENDAR_ID, eventId=event_id))


def reschedule_appointment(event_id: str, new_start_dt: datetime, duration_minutes: int = 30) -> str:
    new_start_dt = _localize(new_start_dt)
    new_end_dt = new_start_dt + timedelta(minutes=duration_minutes)
    service = get_calendar_service()

    event = _execute_with_retry(service.events().get(calendarId=CALENDAR_ID, eventId=event_id))
    event["start"] = {"dateTime": new_start_dt.isoformat(), "timeZone": CLINIC_TIMEZONE}
    event["end"] = {"dateTime": new_end_dt.isoformat(), "timeZone": CLINIC_TIMEZONE}

    updated = _execute_with_retry(service.events().update(calendarId=CALENDAR_ID, eventId=event_id, body=event))
    return updated.get("htmlLink", "")