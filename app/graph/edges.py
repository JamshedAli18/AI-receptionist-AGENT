from app.graph.state import ReceptionistState

FAQ_CATEGORIES = {"appointments", "cancellation_policy", "insurance_billing", "hours", "new_patient"}
LOW_CONFIDENCE_THRESHOLD = 0.5


def route_after_intent(state: ReceptionistState) -> str:
    if state.get("is_emergency"):
        return "escalation_node"

    # Stay in an in-progress booking flow regardless of this turn's intent
    if state.get("booking_stage") in {"collecting", "confirming", "confirming_details"}:
        return "booking_node"

    # Stay in an in-progress reschedule/cancel flow regardless of intent
    if state.get("rc_stage") and state.get("rc_stage") != "done":
        return "reschedule_cancel_node"

    category = state.get("detected_category")
    confidence = state.get("intent_confidence", 1.0)

    if category == "book_appointment" and confidence >= LOW_CONFIDENCE_THRESHOLD:
        return "booking_node"

    if category in {"reschedule_appointment", "cancel_appointment"} and confidence >= LOW_CONFIDENCE_THRESHOLD:
        return "reschedule_cancel_node"

    if category == "small_talk" and confidence >= LOW_CONFIDENCE_THRESHOLD:
        return "small_talk_node"

    if category == "unclear" or confidence < LOW_CONFIDENCE_THRESHOLD:
        return "escalation_node"

    if category in FAQ_CATEGORIES:
        return "faq_node"

    return "escalation_node"


def route_after_faq(state: ReceptionistState) -> str:
    if state.get("needs_escalation"):
        return "escalation_node"
    return "end"