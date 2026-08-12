from app.config import groq_client, LLM_MODEL_QUALITY
from app.rag.retrieve import retrieve_context
from app.graph.state import ReceptionistState

RETRIEVAL_CONFIDENCE_THRESHOLD = 0.35   # below this, don't trust the context enough to answer

SYSTEM_PROMPT = """You are a voice receptionist assistant for BrightPath Clinic.
Answer only using the provided context. Never answer clinical questions
(symptoms, medications, test results) — those get escalated separately.
Keep answers short and conversational — this will be spoken aloud. Do not
offer to escalate or transfer the call yourself; that is handled by the system."""


def faq_node(state: ReceptionistState) -> dict:
    query = state["current_message"]
    results = retrieve_context(query, category=state.get("detected_category"))

    top_score = results[0]["score"] if results else 0.0

    if not results or top_score < RETRIEVAL_CONFIDENCE_THRESHOLD:
        # Retrieval didn't find a confident match — route to escalation
        # instead of letting the LLM paper over weak context.
        return {
            "needs_escalation": True,
            "retrieved_chunks": [r["text"] for r in results],
        }

    context = "\n\n".join(r["text"] for r in results)

    completion = groq_client.chat.completions.create(
        model=LLM_MODEL_QUALITY,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
        temperature=0.3,
        max_tokens=200,
    )

    response_text = completion.choices[0].message.content
    return {
        "response_text": response_text,
        "retrieved_chunks": [r["text"] for r in results],
        "needs_escalation": False,
        "transcript": state.get("transcript", []) + [{"role": "assistant", "content": response_text}],
    }