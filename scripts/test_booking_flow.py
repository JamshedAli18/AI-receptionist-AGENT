import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

CALL_SID = "test-booking-001"

# Scripted multi-turn conversation simulating a real caller booking an
# appointment, providing info across several turns like a real phone call.
CONVERSATION = [
    "I'd like to book an appointment",
    "My name is Sarah Malik",
    "My date of birth is March 4th, 1990",
    "It's for a routine checkup",
    "Tomorrow at 2pm works for me",
    "Yes that works",
]


def print_turn(user_input: str, result: dict):
    print(f"\nYou: {user_input}")
    print(f"Assistant: {result['response_text']}")
    print(
        f"[debug] booking_stage={result.get('booking_stage')} "
        f"name={result.get('patient_name')} dob={result.get('date_of_birth')} "
        f"reason={result.get('reason_for_visit')} "
        f"preferred={result.get('preferred_datetime')} "
        f"proposed_slot={result.get('proposed_slot_iso')}"
    )


def run():
    config = {"configurable": {"thread_id": CALL_SID}}

    greeting = greeting_node({})
    print(f"Assistant: {greeting['response_text']}")

    for message in CONVERSATION:
        result = receptionist_graph.invoke(
            {"current_message": message, "call_sid": CALL_SID},
            config=config,
        )
        print_turn(message, result)
        time.sleep(3)


if __name__ == "__main__":
    run()