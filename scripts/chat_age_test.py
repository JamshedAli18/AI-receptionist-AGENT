import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

CALL_SID = "manual-age-test-001"


def main():
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
            f"[debug] booking_stage={result.get('booking_stage')} "
            f"awaiting={result.get('booking_awaiting_field')} "
            f"name={result.get('patient_name')} age={result.get('patient_age')} "
            f"email={result.get('patient_email')} reason={result.get('reason_for_visit')} "
            f"booking_id={result.get('booking_id')}"
        )


if __name__ == "__main__":
    main()