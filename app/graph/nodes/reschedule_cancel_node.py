from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import instructor
from groq import Groq

from app.config import GROQ_API_KEY, LLM_MODEL_FAST
from app.graph.state import ReceptionistState
from app.graph.nodes.llm_utils import call_with_retry, parse_datetime_robust
from app.services.calendar_service import (
    find_appointment_by_booking_id,
    cancel_appointment,
    reschedule_appointment,
    check_availability,
    is_within_business_hours,
)

client = instructor.from_groq(Groq(api_key=GROQ_API_KEY), mode=instructor.Mode.JSON)

MAX_ID_ATTEMPTS = 2
MAX_DATE_PARSE_ATTEMPTS = 2


class RCExtraction(BaseModel):
    booking_id: Optional[str] = Field(None, description="The booking ID the caller stated, normalized like 'BP482913' (letters + digits, no spaces), only if stated this turn")
    new_preferred_datetime: Optional[str] = Field(None, description="Requested new date/time, only if stated this turn")
    confirms_action: Optional[bool] = Field(None, description="True if caller is confirming (yes), False if declining (no), null if not answering a yes/no question")


EXTRACTION_PROMPT = """Extract any new information from the caller's latest
message for a reschedule or cancellation request. Only fill a field if
stated in THIS message — leave others null. Normalize a spoken booking ID
like "B P four eight two nine one three" into "BP482913". Do NOT invent or
guess a booking_id if the caller's message doesn't contain one — leave it
null in that case."""


def extract_rc_info(message: str, stage: str) -> RCExtraction:
    context_note = ""
    if stage == "lookup":
        context_note = "\n\nThe caller was just asked to state their booking ID."
    elif stage == "confirm_details":
        context_note = (
            "\n\nThe caller was just read their appointment details and asked "
            "to confirm this is the correct appointment to act on. This turn "
            "is very unlikely to contain a booking ID — do not invent one."
        )
    elif stage in {"confirming_cancel", "confirming_reschedule"}:
        context_note = (
            "\n\nThe caller was just asked to confirm an action with yes/no. "
            "Interpret 'yes', 'that works', 'correct' as confirms_action=true. "
            "Interpret 'no', 'don't', 'wait' as confirms_action=false. This "
            "turn is very unlikely to contain a booking ID — do not invent one."
        )

    def _call():
        return client.chat.completions.create(
            model=LLM_MODEL_FAST,
            response_model=RCExtraction,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT + context_note},
                {"role": "user", "content": message},
            ],
            temperature=0,
            max_retries=2,
        )

    return call_with_retry(_call)


def reschedule_cancel_node(state: ReceptionistState) -> dict:
    stage_before = state.get("rc_stage", "lookup")
    action = state.get("rc_action") or (
        "cancel" if state.get("detected_category") == "cancel_appointment" else "reschedule"
    )

    extracted = extract_rc_info(state["current_message"], stage_before)

    updates = {"rc_action": action}
    if extracted.booking_id and stage_before == "lookup":
        updates["rc_booking_id"] = extracted.booking_id.upper().replace(" ", "")
    if extracted.new_preferred_datetime:
        updates["rc_new_preferred_datetime"] = extracted.new_preferred_datetime

    merged = {**state, **updates}
    transcript = state.get("transcript", [])

    def reply(text, **extra):
        return {
            **updates,
            **extra,
            "response_text": text,
            "transcript": transcript + [{"role": "assistant", "content": text}],
        }

    if stage_before == "lookup":
        booking_id = merged.get("rc_booking_id")
        if not booking_id:
            message = "Sure — could you give me your booking ID? It starts with BP followed by six digits."
            return reply(message, rc_stage="lookup")

        appointment = find_appointment_by_booking_id(booking_id)
        attempts = state.get("rc_id_attempts", 0)

        if not appointment:
            attempts += 1
            if attempts >= MAX_ID_ATTEMPTS:
                message = "I still can't find an appointment with that ID. Let me connect you with staff to help."
                return reply(message, rc_stage="done", rc_id_attempts=attempts, escalated=True)

            message = f"I couldn't find an appointment with the ID {booking_id} — could you double check it and say it again?"
            return reply(message, rc_stage="lookup", rc_booking_id=None, rc_id_attempts=attempts)

        dt = datetime.fromisoformat(appointment["start"])
        action_word = "cancel" if action == "cancel" else "reschedule"
        message = (
            f"I found it — an appointment for {appointment['patient_name']} on "
            f"{dt.strftime('%A, %B %d at %I:%M %p')} for {appointment['reason']}. "
            f"You'd like to {action_word} this one, correct?"
        )
        return reply(message, rc_stage="confirm_details", rc_appointment=appointment, rc_id_attempts=0)

    if stage_before == "confirm_details":
        if extracted.confirms_action is True:
            if action == "cancel":
                message = "Just to be sure — should I go ahead and cancel this appointment?"
                return reply(message, rc_stage="confirming_cancel")
            else:
                message = "Great — what new date and time would you like instead?"
                return reply(message, rc_stage="collecting_new_time")

        if extracted.confirms_action is False:
            message = "No problem — let me connect you with staff to sort out the right appointment."
            return reply(message, rc_stage="done", escalated=True)

        message = "Sorry, is that the correct appointment — yes or no?"
        return reply(message, rc_stage="confirm_details")

    if stage_before == "confirming_cancel":
        if extracted.confirms_action is True:
            cancel_appointment(state["rc_appointment"]["event_id"])
            message = "Your appointment has been cancelled. Anything else I can help with?"
            return reply(message, rc_stage="done", escalated=False)
        if extracted.confirms_action is False:
            message = "Okay, I've left that appointment as is. Anything else I can help with?"
            return reply(message, rc_stage="done", escalated=False)
        message = "Sorry, should I go ahead and cancel — yes or no?"
        return reply(message, rc_stage="confirming_cancel")

    if stage_before == "collecting_new_time":
        if not merged.get("rc_new_preferred_datetime"):
            message = "What new date and time would work for you?"
            return reply(message, rc_stage="collecting_new_time")

        parsed_dt = parse_datetime_robust(merged["rc_new_preferred_datetime"])
        attempts = state.get("rc_date_parse_attempts", 0)

        if not parsed_dt:
            attempts += 1
            if attempts >= MAX_DATE_PARSE_ATTEMPTS:
                message = "I'm having trouble understanding the new time — let me connect you with staff to finish this."
                return reply(message, rc_stage="done", rc_date_parse_attempts=attempts, escalated=True)

            message = "I didn't catch that date and time — could you say it again, like 'next Tuesday at 3pm'?"
            return reply(message, rc_stage="collecting_new_time", rc_new_preferred_datetime=None, rc_date_parse_attempts=attempts)

        if not is_within_business_hours(parsed_dt):
            formatted = parsed_dt.strftime("%A, %B %d at %I:%M %p")
            message = (
                f"I'm sorry, {formatted} is outside our hours — we're open "
                f"Monday to Friday, 9am to 6pm, and Saturday 9am to 1pm. "
                f"Could you choose a different date or time?"
            )
            return reply(message, rc_stage="collecting_new_time", rc_new_preferred_datetime=None)

        if not check_availability(parsed_dt):
            formatted = parsed_dt.strftime("%A, %B %d at %I:%M %p")
            message = f"I'm sorry, {formatted} is already booked. Could you choose a different date or time?"
            return reply(message, rc_stage="collecting_new_time", rc_new_preferred_datetime=None)

        formatted = parsed_dt.strftime("%A, %B %d at %I:%M %p")
        message = f"I can move your appointment to {formatted} — does that work?"
        return reply(message, rc_stage="confirming_reschedule", rc_proposed_slot_iso=parsed_dt.isoformat(), rc_date_parse_attempts=0)

    if stage_before == "confirming_reschedule":
        if extracted.confirms_action is True:
            new_slot = datetime.fromisoformat(state["rc_proposed_slot_iso"])

            if not check_availability(new_slot):
                message = "I'm sorry, that slot was just taken by someone else. What other date or time would work?"
                return reply(message, rc_stage="collecting_new_time", rc_new_preferred_datetime=None, rc_proposed_slot_iso=None)

            reschedule_appointment(state["rc_appointment"]["event_id"], new_slot)
            message = f"All set — your appointment is now {new_slot.strftime('%A, %B %d at %I:%M %p')}."
            return reply(message, rc_stage="done", escalated=False)
        if extracted.confirms_action is False:
            message = "No problem — what other date and time would work?"
            return reply(message, rc_stage="collecting_new_time", rc_new_preferred_datetime=None, rc_proposed_slot_iso=None)
        message = "Sorry, does that new time work for you — yes or no?"
        return reply(message, rc_stage="confirming_reschedule")

    message = "Let me connect you with staff to help with that."
    return reply(message, rc_stage="done", escalated=True)