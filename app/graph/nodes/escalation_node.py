from app.graph.state import ReceptionistState
from app.services.patient_service import log_escalation

EMERGENCY_MESSAGE = (
    "This sounds like it could be a medical emergency. Please hang up and call "
    "911 right away, or go to your nearest emergency room."
)

GENERAL_ESCALATION_MESSAGE = (
    "Let me connect you with a member of our staff who can help with that."
)


def escalation_node(state: ReceptionistState) -> dict:
    is_emergency = state.get("is_emergency", False)
    message = EMERGENCY_MESSAGE if is_emergency else GENERAL_ESCALATION_MESSAGE

    log_escalation(
        call_sid=state.get("call_sid", "unknown"),
        reason="emergency" if is_emergency else "general",
        category=state.get("detected_category"),
        message=state.get("current_message", ""),
    )

    return {
        "response_text": message,
        "escalated": True,
        "transcript": state.get("transcript", []) + [{"role": "assistant", "content": message}],
    }