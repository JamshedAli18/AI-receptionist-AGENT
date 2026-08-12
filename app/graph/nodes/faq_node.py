from app.config import groq_client, LLM_MODEL_QUALITY
from app.rag.retrieve import retrieve_context
from app.graph.state import ReceptionistState
from app.graph.nodes.llm_utils import call_with_retry

RETRIEVAL_CONFIDENCE_THRESHOLD = 0.35

SYSTEM_PROMPT = """You are a voice receptionist assistant for BrightPath Clinic.
Answer only using the provided context. Never answer clinical questions
(symptoms, medications, test results) — those get escalated separately.
Keep answers short and conversational — this will be spoken aloud. Do not
offer to escalate or transfer the call yourself; that is handled by the system."""


def generate_faq_answer(query: str, category: str | None) -> tuple[str | None, bool]:
    """
    Shared FAQ-answering logic used by faq_node and, when a caller goes
    off-topic mid reschedule/cancel, by reschedule_cancel_node too.
    Returns (answer_text_or_None, needs_escalation).
    If needs_escalation is True, answer_text_or_None is None — the caller
    is responsible for handling escalation themselves.
    """
    results = retrieve_context(query, category=category)
    top_score = results[0]["score"] if results else 0.0

    if not results or top_score < RETRIEVAL_CONFIDENCE_THRESHOLD:
        return None, True

    context = "\n\n".join(r["text"] for r in results)

    def _call():
        return groq_client.chat.completions.create(
            model=LLM_MODEL_QUALITY,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ],
            temperature=0.3,
            max_tokens=200,
        )

    completion = call_with_retry(_call)
    return completion.choices[0].message.content, False


def faq_node(state: ReceptionistState) -> dict:
    query = state["current_message"]
    answer, needs_escalation = generate_faq_answer(query, state.get("detected_category"))
    transcript = state.get("transcript", [])

    if needs_escalation:
        return {
            "needs_escalation": True,
            "retrieved_chunks": [],
        }

    return {
        "response_text": answer,
        "retrieved_chunks": [],
        "needs_escalation": False,
        "transcript": transcript + [{"role": "assistant", "content": answer}],
    }