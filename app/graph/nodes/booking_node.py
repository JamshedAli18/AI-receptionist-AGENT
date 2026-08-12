from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import instructor
from groq import Groq

from app.config import GROQ_API_KEY, LLM_MODEL_FAST
from app.graph.state import ReceptionistState
from app.graph.nodes.validators import is_valid_email, is_valid_name, is_valid_age, is_valid_reason
from app.graph.nodes.llm_utils import call_with_retry, parse_datetime_robust
from app.services.calendar_service import check_availability, is_within_business_hours, create_appointment

client = instructor.from_groq(Groq(api_key=GROQ_API_KEY), mode=instructor.Mode.JSON)

MAX_DATE_PARSE_ATTEMPTS = 2

FIELD_LABELS = {
    "patient_name": "their full name",
    "patient_age": "their age",
    "patient_email": "their email address",
    "reason_for_visit": "the reason for their visit",
    "preferred_datetime": "their preferred date and time",
}

FIELD_VALIDATORS = {
    "patient_name": is_valid_name,
    "patient_age": is_valid_age,
    "patient_email": is_valid_email,
    "reason_for_visit": is_valid_reason,
}

REQUIRED_FIELDS = [
    ("patient_name", "your full name"),
    ("patient_age", "your age"),
    ("patient_email", "your email address"),
    ("reason_for_visit", "the reason for your visit"),
    ("preferred_datetime", "your preferred date and time"),
]

INVALID_MESSAGES = {
    "patient_name": "That doesn't quite look like a full name — could you say your first and last name?",
    "patient_age": "I didn't catch a valid age — could you say it again?",
    "patient_email": "That doesn't look like a valid email — could you say it again?",
    "reason_for_visit": "Could you tell me a bit more about the reason for your visit?",
}

FRESH_START_STAGES = {None, "booked", "done"}

BOOKING_RESET_FIELDS = {
    "patient_name": None,
    "patient_age": None,
    "patient_email": None,
    "reason_for_visit": None,
    "preferred_datetime": None,
    "proposed_slot_iso": None,
    "booking_id": None,
    "date_parse_attempts": 0,
    "booking_awaiting_field": None,
}


class BookingExtraction(BaseModel):
    patient_name: Optional[str] = Field(None, description="Caller's full name, only if stated this turn")
    patient_age: Optional[str] = Field(None, description="Caller's age as a number, only if stated this turn")
    patient_email: Optional[str] = Field(None, description="Caller's email address, only if stated this turn")
    reason_for_visit: Optional[str] = Field(None, description="Reason for the visit, only if stated this turn")
    preferred_datetime: Optional[str] = Field(None, description="Requested date/time in the caller's own words, only if stated this turn")
    wants_to_confirm: Optional[bool] = Field(None, description="True if caller is confirming a proposed slot, False if declining, null if not answering a confirmation question")


EXTRACTION_PROMPT = """Extract any new booking details from the caller's latest
message. Only fill a field if it was actually stated in THIS message — leave
others null. Do not guess or carry over information from earlier turns.

IMPORTANT: A message that only expresses wanting to book or schedule an
appointment (e.g. "I'd like to book an appointment") is NOT a reason for
visit — leave reason_for_visit null for such messages.

CRITICAL: A single message may legitimately contain several fields at once
(e.g. "I'm Alex Johnson, 34 years old, and my email is alex@x.com") —
extract all of them in that case. Only fill a field if the message clearly
states it; don't guess or infer a value that wasn't actually said."""


def extract_booking_info(message: str, booking_stage: str, awaiting_fields: Optional[list]) -> BookingExtraction:
    context_note = ""
    if booking_stage == "confirming":
        context_note = (
            "\n\nIMPORTANT: The caller was just offered a specific appointment "
            "slot and asked if it works for them. Interpret words like 'yes', "
            "'that works', 'sounds good', or 'sure' as wants_to_confirm=true. "
            "Interpret 'no', 'that doesn't work', or a different time request "
            "as wants_to_confirm=false."
        )
    elif awaiting_fields:
        labels = [FIELD_LABELS.get(f, f) for f in awaiting_fields]
        context_note = (
            f"\n\nThe caller was just asked to provide: {', '.join(labels)}. "
            f"Their message may answer one, several, or all of these at once "
            f"— extract whichever ones are actually present."
        )

    def _call():
        return client.chat.completions.create(
            model=LLM_MODEL_FAST,
            response_model=BookingExtraction,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT + context_note},
                {"role": "user", "content": message},
            ],
            temperature=0,
            max_retries=2,
        )

    return call_with_retry(_call)


def missing_or_invalid_fields(state: dict) -> list[tuple[str, str]]:
    results = []
    for field, label in REQUIRED_FIELDS:
        value = state.get(field)
        validator = FIELD_VALIDATORS.get(field)
        if not value:
            results.append((field, label))
        elif validator and not validator(value):
            results.append((field, label))
    return results


def build_missing_fields_message(missing: list[tuple[str, str]]) -> str:
    labels = [label for _, label in missing]
    if len(labels) == 1:
        return f"Could you tell me {labels[0]}?"
    if len(labels) == 2:
        return f"Could you tell me {labels[0]} and {labels[1]}?"
    return f"Could you tell me {', '.join(labels[:-1])}, and {labels[-1]}?"


def booking_node(state: ReceptionistState) -> dict:
    stage_before = state.get("booking_stage")
    is_fresh_start = stage_before in FRESH_START_STAGES

    reset_fields = dict(BOOKING_RESET_FIELDS) if is_fresh_start else {}
    effective_stage = "collecting" if is_fresh_start else stage_before
    awaiting_fields = None if is_fresh_start else state.get("booking_awaiting_field")

    extracted = extract_booking_info(state["current_message"], effective_stage, awaiting_fields)

    updates = dict(reset_fields)
    for field in ["patient_name", "patient_age", "patient_email", "reason_for_visit", "preferred_datetime"]:
        value = getattr(extracted, field)
        if not value:
            continue
        validator = FIELD_VALIDATORS.get(field)
        if validator and not validator(value):
            continue
        updates[field] = value

    merged_state = {**state, **updates}
    stage = "confirming" if (not is_fresh_start and stage_before == "confirming") else "collecting"
    transcript = state.get("transcript", [])

    def reply(text, **extra):
        return {
            **updates,
            **extra,
            "response_text": text,
            "transcript": transcript + [{"role": "assistant", "content": text}],
        }

    if stage == "confirming":
        if extracted.wants_to_confirm is True and merged_state.get("proposed_slot_iso"):
            slot_dt = datetime.fromisoformat(merged_state["proposed_slot_iso"])

            if not check_availability(slot_dt):
                message = "I'm sorry, that slot was just taken by someone else. Could you choose a different date or time?"
                return reply(message, booking_stage="collecting", preferred_datetime=None, proposed_slot_iso=None, booking_awaiting_field=["preferred_datetime"])

            result = create_appointment(
                start_dt=slot_dt,
                patient_name=merged_state["patient_name"],
                reason=merged_state["reason_for_visit"],
            )
            booking_id = result["booking_id"]
            message = (
                f"You're all set — booked for {slot_dt.strftime('%A, %B %d at %I:%M %p')}. "
                f"Your booking ID is {booking_id} — please save this, you'll need it if you "
                f"want to reschedule or cancel later. A confirmation will be sent to your email."
            )
            return reply(message, booking_stage="booked", booking_id=booking_id, booking_awaiting_field=None)

        if extracted.wants_to_confirm is False:
            message = "No problem — what date and time would work better for you?"
            return reply(
                message,
                booking_stage="collecting",
                preferred_datetime=None,
                proposed_slot_iso=None,
                booking_awaiting_field=["preferred_datetime"],
            )

        message = "Sorry, just to confirm — does that time work for you?"
        return reply(message, booking_stage="confirming")

    missing = missing_or_invalid_fields(merged_state)
    if missing:
        if len(missing) == 1 and merged_state.get(missing[0][0]) and INVALID_MESSAGES.get(missing[0][0]):
            message = INVALID_MESSAGES[missing[0][0]]
        else:
            message = build_missing_fields_message(missing)

        if is_fresh_start:
            # On the very first turn, the overview already lists everything
            # needed — don't also repeat it in question form right after.
            message = (
                "Sure, I can help you book an appointment. I'll need your full "
                "name, age, email address, the reason for your visit, and your "
                "preferred date and time — you can give me all of that, or just "
                "start with your name."
            )

        return reply(message, booking_stage="collecting", booking_awaiting_field=[f for f, _ in missing])

    parsed_dt = parse_datetime_robust(merged_state["preferred_datetime"])

    attempts = state.get("date_parse_attempts", 0) if not is_fresh_start else 0

    if not parsed_dt:
        attempts += 1
        if attempts >= MAX_DATE_PARSE_ATTEMPTS:
            message = "I'm having trouble understanding the date and time — let me connect you with staff to finish booking."
            return reply(message, date_parse_attempts=attempts, booking_stage="done", escalated=True)

        message = "I didn't quite catch that date and time — could you say it again, like 'next Tuesday at 3pm'?"
        return reply(message, preferred_datetime=None, date_parse_attempts=attempts, booking_awaiting_field=["preferred_datetime"], booking_stage="collecting")

    if not is_within_business_hours(parsed_dt):
        formatted = parsed_dt.strftime("%A, %B %d at %I:%M %p")
        message = (
            f"I'm sorry, {formatted} is outside our hours — we're open "
            f"Monday to Friday, 9am to 6pm, and Saturday 9am to 1pm. "
            f"Could you choose a different date or time?"
        )
        return reply(message, preferred_datetime=None, booking_awaiting_field=["preferred_datetime"], booking_stage="collecting")

    if not check_availability(parsed_dt):
        formatted = parsed_dt.strftime("%A, %B %d at %I:%M %p")
        message = f"I'm sorry, {formatted} is already booked. Could you choose a different date or time?"
        return reply(message, preferred_datetime=None, booking_awaiting_field=["preferred_datetime"], booking_stage="collecting")

    formatted = parsed_dt.strftime("%A, %B %d at %I:%M %p")
    message = f"I have {formatted} available — does that work for you?"
    return reply(
        message,
        booking_stage="confirming",
        proposed_slot_iso=parsed_dt.isoformat(),
        date_parse_attempts=0,
    )