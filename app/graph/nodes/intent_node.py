from typing import Literal
from pydantic import BaseModel, Field
import instructor
from groq import Groq
from instructor.v2.core.errors import IncompleteOutputException

from app.config import GROQ_API_KEY, LLM_MODEL_FAST
from app.graph.state import ReceptionistState
from app.graph.nodes.llm_utils import call_with_retry

client = instructor.from_groq(Groq(api_key=GROQ_API_KEY), mode=instructor.Mode.TOOLS)


class IntentClassification(BaseModel):
    category: Literal[
        "book_appointment",
        "reschedule_appointment",
        "cancel_appointment",
        "appointments",
        "cancellation_policy",
        "insurance_billing",
        "hours",
        "new_patient",
        "small_talk",
        "unclear",
    ] = Field(description="Best-matching category for the caller's message")

    is_emergency: bool = Field(
        description="True if the caller describes symptoms like chest pain, "
        "difficulty breathing, severe bleeding, or loss of consciousness — "
        "checked independently of category, never inferred from it"
    )

    confidence: float = Field(
        ge=0.0, le=1.0,
        description="How confident you are in the category classification, 0 to 1"
    )


INTENT_SYSTEM_PROMPT = """You classify a caller's message for a medical clinic
voice receptionist. Always fill in is_emergency independently — it is a
separate safety check, not derived from the category.

Use "book_appointment" for a NEW appointment request. Use
"reschedule_appointment" when the caller wants to change the time of an
EXISTING appointment. Use "cancel_appointment" when they want to cancel an
existing one. Use "appointments" only for general questions about types or
policies, not an actual booking/reschedule/cancel request.

Use "small_talk" ONLY for pure greetings or pleasantries with no actual
question or request in them. If the message asks about or references any
clinic fact — staff, services, hours, policies, billing, or a specific
provider — classify it into the matching category instead.

Use "unclear" only when the caller seems to want help but you can't tell
what kind. Set confidence honestly.

Respond with ONLY the JSON object — no explanation, no reasoning, no extra
text before or after it."""


def _classify(message: str) -> IntentClassification:
    def _call():
        return client.chat.completions.create(
            model=LLM_MODEL_FAST,
            response_model=IntentClassification,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0,
            max_tokens=500,
            max_retries=2,
        )

    return call_with_retry(_call)


def intent_node(state: ReceptionistState) -> dict:
    try:
        result = _classify(state["current_message"])
        category = result.category
        is_emergency = result.is_emergency
        confidence = result.confidence
    except IncompleteOutputException:
        # If the model's structured output keeps getting truncated even
        # after retries, don't crash the whole call — degrade gracefully.
        # "unclear" with low confidence routes to escalation_node, which is
        # the safe, honest fallback rather than dropping the caller.
        print("[intent_node] Classification failed after retries, falling back to unclear/escalation.")
        category = "unclear"
        is_emergency = False
        confidence = 0.0

    return {
        "detected_category": category,
        "is_emergency": is_emergency,
        "intent_confidence": confidence,
        "escalated": False,
        "needs_escalation": False,
        "transcript": state.get("transcript", []) + [{"role": "user", "content": state["current_message"]}],
    }