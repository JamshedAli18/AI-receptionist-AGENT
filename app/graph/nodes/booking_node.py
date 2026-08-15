from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import instructor
from groq import Groq

from app.config import GROQ_API_KEY, LLM_MODEL_FAST
from app.graph.state import ReceptionistState
from app.graph.nodes.validators import is_valid_email, is_valid_name, is_valid_age, is_valid_reason, normalize_spoken_email, _extract_email
from app.graph.nodes.llm_utils import call_with_retry, parse_datetime_robust, detect_confirmation_fallback, detect_abandonment_fallback
from app.mcp.calendar_tools import check_availability, is_within_business_hours, create_appointment
from app.services.patient_service import log_appointment_created
from app.mcp.email_tools import notify_clinic_new_booking, send_patient_booking_confirmation

client = instructor.from_groq(Groq(api_key=GROQ_API_KEY), mode=instructor.Mode.TOOLS)

MAX_DATE_PARSE_ATTEMPTS = 2
MAX_CONFIRMATION_ATTEMPTS = 3

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
    "booking_confirmation_attempts": 0,
}


class BookingExtraction(BaseModel):
    patient_name: Optional[str] = Field(None, description="Caller's full name, only if stated this turn")
    patient_age: Optional[str] = Field(None, description="Caller's age as a number, only if stated this turn")
    patient_email: Optional[str] = Field(None, description="Caller's email address, only if stated this turn")
    reason_for_visit: Optional[str] = Field(None, description="Reason for the visit, only if stated this turn")
    preferred_datetime: Optional[str] = Field(None, description="Requested date/time in the caller's own words, only if stated this turn")
    wants_to_confirm: Optional[bool] = Field(None, description="True if caller is confirming something asked, False if declining/correcting, null if not answering a confirmation question")
    wants_to_abandon: Optional[bool] = Field(None, description="True if the caller wants to stop/exit the booking process entirely — e.g. says bye, never mind, changed their mind, not interested, doesn't want to book anymore")


EXTRACTION_PROMPT = """Extract any new booking details from the caller's latest
message. Only fill a field if it was actually stated in THIS message — leave
others null. Do not guess or carry over information from earlier turns.

IMPORTANT: A message that only expresses wanting to book or schedule an
appointment (e.g. "I'd like to book an appointment") is NOT a reason for
visit — leave reason_for_visit null for such messages.

CRITICAL: A single message may legitimately contain several fields at once,
including corrections to previously given information — extract all of them.
Only fill a field if the message clearly states it; don't guess.

Set wants_to_abandon=true if the caller indicates they want to stop the
booking process — saying goodbye, "never mind", "I don't want to book",
"forget it", "leave it", "actually no", or similar. This should be checked
independently on every message, regardless of what else is in it.

Recognize casual affirmatives like 'yeah', 'yep', 'sure', 'okay', 'that's
right', 'correct' as wants_to_confirm=true. Recognize 'no', 'wrong',
'that's not right', 'incorrect' as wants_to_confirm=false — if the caller
also restates a corrected value in the same message, capture it in the
relevant field too."""


def extract_booking_info(message: str, booking_stage: str, awaiting_fields: Optional[list]) -> BookingExtraction:
    context_note = ""
    if booking_stage == "confirming":
        context_note = (
            "\n\nIMPORTANT: The caller was just offered a specific appointment "
            "slot and asked if it works for them. Interpret confirmations as "
            "wants_to_confirm=true, declines as false."
        )
    elif booking_stage == "confirming_details":
        context_note = (
            "\n\nIMPORTANT: The caller was just read back a full summary of "
            "their booking details (name, age, email, reason, date/time) and "
            "asked if everything is correct. 'Yes'/'correct' = "
            "wants_to_confirm=true. 'No' or naming something wrong = "
            "wants_to_confirm=false — capture any corrected value they give "
            "in the same message (e.g. 'no, my email is actually x@y.com')."
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
            max_tokens=500,
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


def build_summary_message(state: dict) -> str:
    return (
        f"Let me confirm what I have: {state['patient_name']}, age {state['patient_age']}, "
        f"email {state['patient_email']}, for {state['reason_for_visit']}, "
        f"preferred time {state['preferred_datetime']}. Is all of that correct?"
    )


def booking_node(state: ReceptionistState) -> dict:
    stage_before = state.get("booking_stage")
    is_fresh_start = stage_before in FRESH_START_STAGES

    reset_fields = dict(BOOKING_RESET_FIELDS) if is_fresh_start else {}
    effective_stage = "collecting" if is_fresh_start else stage_before
    awaiting_fields = None if is_fresh_start else state.get("booking_awaiting_field")

    extracted = extract_booking_info(state["current_message"], effective_stage, awaiting_fields)

    # Check for abandonment first, before anything else — a caller trying
    # to exit the booking flow must always be able to, regardless of stage.
    wants_to_abandon = extracted.wants_to_abandon
    if wants_to_abandon is None and not is_fresh_start:
        wants_to_abandon = detect_abandonment_fallback(state["current_message"])

    if wants_to_abandon:
        message = "No problem, I won't book anything. Is there anything else I can help you with?"
        return {
            "response_text": message,
            "booking_stage": "done",
            "booking_awaiting_field": None,
            "patient_name": None,
            "patient_age": None,
            "patient_email": None,
            "reason_for_visit": None,
            "preferred_datetime": None,
            "proposed_slot_iso": None,
            "escalated": False,
            "transcript": state.get("transcript", []) + [{"role": "assistant", "content": message}],
        }

    updates = dict(reset_fields)
    for field in ["patient_name", "patient_age", "patient_email", "reason_for_visit", "preferred_datetime"]:
        value = getattr(extracted, field)

        if field == "patient_email":
            # Prefer deterministic regex extraction straight from the raw
            # transcript — more reliable for "X at Y dot Z" voice patterns
            # than hoping the LLM extraction preserved it correctly.
            regex_email = _extract_email(state["current_message"])
            if regex_email:
                value = regex_email
            elif value:
                value = normalize_spoken_email(value)

        if not value:
            continue

        validator = FIELD_VALIDATORS.get(field)
        if validator and not validator(value):
            continue
        updates[field] = value

    merged_state = {**state, **updates}
    stage = effective_stage if not is_fresh_start else "collecting"
    transcript = state.get("transcript", [])

    def reply(text, **extra):
        return {
            **updates,
            **extra,
            "response_text": text,
            "transcript": transcript + [{"role": "assistant", "content": text}],
        }

    if stage == "confirming":
        wants_to_confirm = extracted.wants_to_confirm
        if wants_to_confirm is None:
            wants_to_confirm = detect_confirmation_fallback(state["current_message"])

        if wants_to_confirm is True and merged_state.get("proposed_slot_iso"):
            slot_dt = datetime.fromisoformat(merged_state["proposed_slot_iso"])

            if not check_availability(slot_dt):
                message = "I'm sorry, that slot was just taken by someone else. Could you choose a different date or time?"
                return reply(message, booking_stage="collecting", preferred_datetime=None, proposed_slot_iso=None, booking_awaiting_field=["preferred_datetime"])

            result = create_appointment(
                start_dt=slot_dt,
                patient_name=merged_state["patient_name"],
                patient_email=merged_state["patient_email"],
                reason=merged_state["reason_for_visit"],
            )
            booking_id = result["booking_id"]

            log_appointment_created(
                booking_id=booking_id,
                event_id=result["event_id"],
                patient_name=merged_state["patient_name"],
                patient_age=merged_state["patient_age"],
                patient_email=merged_state["patient_email"],
                reason=merged_state["reason_for_visit"],
                scheduled_time=slot_dt,
            )

            notify_clinic_new_booking(
                booking_id, merged_state["patient_name"], merged_state["patient_age"],
                merged_state["patient_email"], merged_state["reason_for_visit"], slot_dt,
            )
            send_patient_booking_confirmation(
                merged_state["patient_email"], merged_state["patient_name"],
                booking_id, slot_dt, merged_state["reason_for_visit"],
            )

            message = (
                f"You're all set — booked for {slot_dt.strftime('%A, %B %d at %I:%M %p')}. "
                f"Your booking ID is {booking_id} — please save this, you'll need it if you "
                f"want to reschedule or cancel later. A confirmation will be sent to your email."
            )
            return reply(message, booking_stage="booked", booking_id=booking_id, booking_awaiting_field=None)

        if wants_to_confirm is False:
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

    if stage == "confirming_details":
        wants_to_confirm = extracted.wants_to_confirm
        if wants_to_confirm is None:
            wants_to_confirm = detect_confirmation_fallback(state["current_message"])

        if wants_to_confirm is True:
            # Fall through below to date parsing / availability, using the
            # now-confirmed field values.
            pass
        elif wants_to_confirm is False:
            attempts = state.get("booking_confirmation_attempts", 0) + 1

            if attempts >= MAX_CONFIRMATION_ATTEMPTS:
                message = "I'm having trouble getting these details right — let me connect you with staff to finish this."
                return reply(message, booking_stage="done", escalated=True, booking_confirmation_attempts=attempts)

            # If the caller already restated a corrected value in this same
            # message, it's already in `updates` above — just re-summarize
            # with the new values. If they didn't specify anything, ask
            # what needs fixing.
            any_field_changed = any(
                getattr(extracted, f) for f in ["patient_name", "patient_age", "patient_email", "reason_for_visit", "preferred_datetime"]
            )
            if any_field_changed:
                message = build_summary_message(merged_state)
                return reply(message, booking_stage="confirming_details", booking_confirmation_attempts=attempts)

            message = "No problem — what would you like to correct? You can tell me your name, age, email, reason for visit, or date and time."
            return reply(message, booking_stage="collecting", booking_confirmation_attempts=attempts, booking_awaiting_field=None)
        else:
            message = build_summary_message(merged_state)
            return reply(message, booking_stage="confirming_details")

    missing = missing_or_invalid_fields(merged_state)
    if missing:
        if len(missing) == 1 and merged_state.get(missing[0][0]) and INVALID_MESSAGES.get(missing[0][0]):
            message = INVALID_MESSAGES[missing[0][0]]
        else:
            message = build_missing_fields_message(missing)

        if is_fresh_start:
            message = (
                "Sure, I can help you book an appointment. I'll need your full "
                "name, age, email address, the reason for your visit, and your "
                "preferred date and time — you can give me all of that, or just "
                "start with your name."
            )

        return reply(message, booking_stage="collecting", booking_awaiting_field=[f for f, _ in missing])

    # All fields present and valid. If we haven't yet read the full summary
    # back for confirmation this round, do that now before touching the
    # calendar at all.
    if stage != "confirming_details" or extracted.wants_to_confirm is not True:
        if stage == "collecting":
            message = build_summary_message(merged_state)
            return reply(message, booking_stage="confirming_details")

    parsed_dt = parse_datetime_robust(merged_state["preferred_datetime"])

    attempts = state.get("date_parse_attempts", 0) if not is_fresh_start else 0

    if not parsed_dt:
        attempts += 1
        if attempts >= MAX_DATE_PARSE_ATTEMPTS:
            message = "I'm having trouble understanding the date and time — let me connect you with staff to finish booking."
            return reply(message, date_parse_attempts=attempts, booking_stage="done", escalated=True)

        message = "I didn't quite catch that date and time — could you say it again, like 'next Tuesday at 3pm'?"
        return reply(message, preferred_datetime=None, date_parse_attempts=attempts, booking_awaiting_field=["preferred_datetime"], booking_stage="collecting")

    if parsed_dt < datetime.now():
        formatted = parsed_dt.strftime("%A, %B %d at %I:%M %p")
        message = f"I'm sorry, {formatted} has already passed. Could you give me a date and time in the future?"
        return reply(message, preferred_datetime=None, booking_awaiting_field=["preferred_datetime"], booking_stage="collecting")

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