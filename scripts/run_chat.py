import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

CALL_SID = "test-call-002"   # fresh thread so this run isn't influenced by the earlier conversation

# Only the questions that exercise faq_node's retrieval + rerank path —
# the ones that hit the Cohere rate limit last time.
TEST_QUESTIONS = [
    "I'm not sure, it's about my last visit",
    "Something's wrong with my bill I think",
    "I need to cancel but it's been like a week since I was supposed to come in",
    "Do you have a pediatric dentist on staff?",
    "If I no-show twice will you guys drop me as a patient?",
]


def print_turn(user_input: str, result: dict):
    print(f"\nYou: {user_input}")
    print(f"Assistant: {result['response_text']}")
    print(
        f"[debug] category={result.get('detected_category')} "
        f"confidence={result.get('intent_confidence')} "
        f"is_emergency={result.get('is_emergency')} "
        f"needs_escalation={result.get('needs_escalation')} "
        f"escalated={result.get('escalated')}"
    )


def run_batch():
    config = {"configurable": {"thread_id": CALL_SID}}

    greeting = greeting_node({})
    print(f"Assistant: {greeting['response_text']}")

    for question in TEST_QUESTIONS:
        result = receptionist_graph.invoke(
            {"current_message": question, "call_sid": CALL_SID},
            config=config,
        )
        print_turn(question, result)
        time.sleep(10)   # each faq_node turn can burn 2-3 Cohere calls (embed + up to 2 rerank);
                          # trial limit is 10/min across the whole account, so pace conservatively


def run_interactive():
    config = {"configurable": {"thread_id": CALL_SID}}

    greeting = greeting_node({})
    print(f"\nAssistant: {greeting['response_text']}")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"quit", "exit", "bye"}:
            print("\nAssistant: Thanks for calling BrightPath Clinic. Take care!")
            break

        result = receptionist_graph.invoke(
            {"current_message": user_input, "call_sid": CALL_SID},
            config=config,
        )
        print(f"\nAssistant: {result['response_text']}")
        print(
            f"[debug] category={result.get('detected_category')} "
            f"confidence={result.get('intent_confidence')} "
            f"is_emergency={result.get('is_emergency')} "
            f"needs_escalation={result.get('needs_escalation')} "
            f"escalated={result.get('escalated')}"
        )


if __name__ == "__main__":
    if "--interactive" in sys.argv or "-i" in sys.argv:
        run_interactive()
    else:
        run_batch()