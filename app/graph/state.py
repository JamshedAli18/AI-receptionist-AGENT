from typing import TypedDict, Optional


class ReceptionistState(TypedDict, total=False):
    call_sid: str
    caller_number: str
    current_message: str
    transcript: list[dict]

    detected_category: Optional[str]
    is_emergency: bool
    intent_confidence: float
    retrieved_chunks: list[str]
    needs_escalation: bool

    # Booking flow (new appointments)
    patient_name: Optional[str]
    patient_age: Optional[str]
    patient_email: Optional[str]
    reason_for_visit: Optional[str]
    preferred_datetime: Optional[str]
    booking_stage: Optional[str]
    booking_awaiting_field: Optional[list]
    proposed_slot_iso: Optional[str]
    confirmed: Optional[bool]
    booking_id: Optional[str]
    date_parse_attempts: int

    # Reschedule / cancel flow
    rc_action: Optional[str]
    rc_stage: Optional[str]
    rc_booking_id: Optional[str]
    rc_id_attempts: int
    rc_appointment: Optional[dict]
    rc_new_preferred_datetime: Optional[str]
    rc_proposed_slot_iso: Optional[str]
    rc_date_parse_attempts: int

    response_text: str
    escalated: bool
    call_ended: bool

    booking_confirmation_attempts: int