from app.config import groq_client, LLM_MODEL_FAST
from app.graph.state import ReceptionistState
from app.graph.nodes.llm_utils import call_with_retry

SYSTEM_PROMPT = """You are a voice receptionist for BrightPath Clinic responding
to small talk or a greeting — not a real question. Reply warmly in one short
sentence, then prompt them toward why they're calling.

You must never state facts about the clinic (staff, services, hours, policies,
pricing) — you have no access to that information here. If the caller's
message contains any real question or request, do not answer it yourself;
just acknowledge and ask them to tell you more about what they need."""


def small_talk_node(state: ReceptionistState) -> dict:
    def _call():
        return groq_client.chat.completions.create(
            model=LLM_MODEL_FAST,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": state["current_message"]},
            ],
            temperature=0.5,
            max_tokens=60,
        )

    completion = call_with_retry(_call)
    response_text = completion.choices[0].message.content
    return {
        "response_text": response_text,
        "escalated": False,
        "needs_escalation": False,
        "transcript": state.get("transcript", []) + [{"role": "assistant", "content": response_text}],
    }