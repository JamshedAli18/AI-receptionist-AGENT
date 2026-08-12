# scripts/test_full_system.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

CALL_SID = "full-system-test"


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
            f"[debug] category={result.get('detected_category')} "
            f"is_emergency={result.get('is_emergency')} "
            f"escalated={result.get('escalated')} "
            f"booking_stage={result.get('booking_stage')} "
            f"rc_stage={result.get('rc_stage')} "
            f"booking_id={result.get('booking_id')}"
        )


if __name__ == "__main__":
    main()