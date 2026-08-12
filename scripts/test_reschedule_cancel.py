# scripts/test_reschedule_cancel.py
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

PAUSE = 3  # seconds between turns, keeps Groq/Cohere calls under rate limits


def print_turn(user_input: str, result: dict, booking_debug: bool = False):
    print(f"\nYou: {user_input}")
    print(f"Assistant: {result['response_text']}")
    if booking_debug:
        print(
            f"[debug] booking_stage={result.get('booking_stage')} "
            f"booking_id={result.get('booking_id')}"
        )
    else:
        print(
            f"[debug] rc_action={result.get('rc_action')} rc_stage={result.get('rc_stage')} "
            f"rc_booking_id={result.get('rc_booking_id')} "
            f"appointment={result.get('rc_appointment')} "
            f"proposed_slot={result.get('rc_proposed_slot_iso')} "
            f"escalated={result.get('escalated')}"
        )


def run_conversation(call_sid: str, turns: list[str], booking_debug: bool = False) -> dict:
    """Returns the final result dict, so callers can pull out things like booking_id."""
    config = {"configurable": {"thread_id": call_sid}}
    greeting = greeting_node({})
    print(f"\n{'='*70}\nCALL: {call_sid}\n{'='*70}")
    print(f"Assistant: {greeting['response_text']}")

    result = {}
    for message in turns:
        result = receptionist_graph.invoke(
            {"current_message": message, "call_sid": call_sid},
            config=config,
        )
        print_turn(message, result, booking_debug=booking_debug)
        time.sleep(PAUSE)
    return result


def book_appointment(call_sid: str, name: str, dob: str, reason: str, when: str) -> str | None:
    """Books an appointment and returns the booking_id extracted from state."""
    turns = [
        "I'd like to book an appointment",
        f"My name is {name}",
        f"My date of birth is {dob}",
        reason,
        when,
        "Yes that works",
    ]
    result = run_conversation(call_sid, turns, booking_debug=True)
    return result.get("booking_id")


def test_reschedule_with_valid_id():
    booking_id = book_appointment(
        "test-resched-book",
        name="Test Patient Reschedule",
        dob="January 1st, 1995",
        reason="It's for a follow-up visit",
        when="Tomorrow at 10am",
    )
    print(f"\n>>> Booked with ID: {booking_id}")

    if not booking_id:
        print(">>> Booking failed, skipping reschedule test")
        return

    turns = [
        "I need to reschedule my appointment",
        f"My booking ID is {booking_id}",
        "Yes that's correct",
        "Can we move it to the day after tomorrow at 11am instead",
        "Yes that works",
    ]
    run_conversation("test-resched-action", turns)


def test_cancel_with_valid_id():
    booking_id = book_appointment(
        "test-cancel-book",
        name="Test Patient Cancel",
        dob="June 15th, 1988",
        reason="Annual physical",
        when="In three days at 9am",
    )
    print(f"\n>>> Booked with ID: {booking_id}")

    if not booking_id:
        print(">>> Booking failed, skipping cancel test")
        return

    turns = [
        "I need to cancel my appointment",
        f"My booking ID is {booking_id}",
        "Yes that's the right one",
        "Yes, please cancel it",
    ]
    run_conversation("test-cancel-action", turns)


def test_invalid_booking_id():
    """Should politely say the ID wasn't found, retry once, then escalate — never crash or hallucinate an appointment."""
    turns = [
        "I need to reschedule my appointment",
        "My booking ID is BP000000",
        "It's B P zero zero zero zero zero one",
    ]
    run_conversation("test-invalid-id", turns)


def test_cancel_declined_at_confirmation():
    """Books, then walks through cancel but says 'no' at the final confirm — appointment should NOT be deleted."""
    booking_id = book_appointment(
        "test-decline-book",
        name="Test Patient Decline",
        dob="May 5th, 1992",
        reason="Sick visit",
        when="In four days at 2pm",
    )
    print(f"\n>>> Booked with ID: {booking_id}")

    if not booking_id:
        print(">>> Booking failed, skipping decline test")
        return

    turns = [
        "I need to cancel my appointment",
        f"My booking ID is {booking_id}",
        "Yes that's correct",
        "No, actually don't cancel it",
    ]
    run_conversation("test-decline-action", turns)
    print(f">>> Booking {booking_id} should STILL exist on the calendar — verify manually")


if __name__ == "__main__":
    test_reschedule_with_valid_id()
    test_cancel_with_valid_id()
    test_invalid_booking_id()
    test_cancel_declined_at_confirmation()