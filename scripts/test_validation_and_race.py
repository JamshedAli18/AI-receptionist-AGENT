# scripts/test_validation_and_race.py
import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

PAUSE = 3


def print_turn(user_input: str, result: dict):
    print(f"\nYou: {user_input}")
    print(f"Assistant: {result['response_text']}")
    print(
        f"[debug] booking_stage={result.get('booking_stage')} "
        f"name={result.get('patient_name')} dob={result.get('date_of_birth')} "
        f"email={result.get('patient_email')} reason={result.get('reason_for_visit')} "
        f"proposed_slot={result.get('proposed_slot_iso')}"
    )


def run_conversation(call_sid: str, turns: list[str]):
    config = {"configurable": {"thread_id": call_sid}}
    greeting = greeting_node({})
    print(f"\n{'='*70}\nCALL: {call_sid}\n{'='*70}")
    print(f"Assistant: {greeting['response_text']}")

    for message in turns:
        result = receptionist_graph.invoke(
            {"current_message": message, "call_sid": call_sid},
            config=config,
        )
        print_turn(message, result)
        time.sleep(PAUSE)
    return result


# ---------------------------------------------------------------------------
# Test 1: invalid email should be rejected and re-asked, not silently accepted
# ---------------------------------------------------------------------------
def test_invalid_email_rejected():
    turns = [
        "I'd like to book an appointment",
        "My name is John Smith",
        "My date of birth is April 10th, 1985",
        "My email is asdf",              # invalid — should be rejected
        "Okay it's john.smith@email.com", # valid — should now be accepted
        "It's for a checkup",
        "Next Wednesday at 2pm",
        "Yes that works",
    ]
    run_conversation("test-invalid-email", turns)


# ---------------------------------------------------------------------------
# Test 2: single-word "name" should be rejected (e.g. caller says "John" only)
# ---------------------------------------------------------------------------
def test_invalid_name_rejected():
    turns = [
        "I'd like to book an appointment",
        "John",                           # invalid — single word, should be rejected
        "My full name is John Rivera",    # valid — should now be accepted
        "My date of birth is July 4th, 1990",
        "john.rivera@email.com",
        "General checkup",
        "Next Thursday at 3pm",
        "Yes that works",
    ]
    run_conversation("test-invalid-name", turns)


# ---------------------------------------------------------------------------
# Test 3: gibberish date of birth should be rejected
# ---------------------------------------------------------------------------
def test_invalid_dob_rejected():
    turns = [
        "I'd like to book an appointment",
        "My name is Maria Lopez",
        "Um, I don't really remember",    # invalid — not a real date, should be rejected
        "It's November 12th, 1978",       # valid — should now be accepted
        "maria.lopez@email.com",
        "Annual physical",
        "Next Friday at 10am",
        "Yes that works",
    ]
    run_conversation("test-invalid-dob", turns)


# ---------------------------------------------------------------------------
# Test 4: double-booking race — two "callers" try to book the exact same
# slot at the same time. The second one should get bumped to the next slot
# instead of silently double-booking.
# ---------------------------------------------------------------------------
def _book_specific_slot(call_sid: str, name: str, slot_phrase: str, results: dict):
    turns = [
        "I'd like to book an appointment",
        f"My name is {name}",
        "My date of birth is January 1st, 1995",
        f"{name.lower().replace(' ', '.')}@email.com",
        "Routine visit",
        slot_phrase,
    ]
    config = {"configurable": {"thread_id": call_sid}}
    greeting_node({})

    result = {}
    for message in turns:
        result = receptionist_graph.invoke(
            {"current_message": message, "call_sid": call_sid},
            config=config,
        )
        print(f"[{call_sid}] You: {message}")
        print(f"[{call_sid}] Assistant: {result['response_text']}\n")

    # Both callers confirm at roughly the same moment
    result = receptionist_graph.invoke(
        {"current_message": "Yes that works", "call_sid": call_sid},
        config=config,
    )
    print(f"[{call_sid}] You: Yes that works")
    print(f"[{call_sid}] Assistant: {result['response_text']}\n")
    results[call_sid] = result


def test_double_booking_race():
    print(f"\n{'='*70}\nDOUBLE-BOOKING RACE TEST\n{'='*70}")
    print("Two simulated callers both try to book Monday at 9am at nearly the same time.\n")

    results = {}
    slot_phrase = "Next Monday at 9am"

    t1 = threading.Thread(target=_book_specific_slot, args=("race-caller-1", "Race Caller One", slot_phrase, results))
    t2 = threading.Thread(target=_book_specific_slot, args=("race-caller-2", "Race Caller Two", slot_phrase, results))

    t1.start()
    time.sleep(1)  # stagger slightly so caller 1 books first, caller 2 hits the race window
    t2.start()

    t1.join()
    t2.join()

    print(f"\n{'='*70}\nRACE TEST RESULTS\n{'='*70}")
    for call_sid, result in results.items():
        booked_time = None
        text = result.get("response_text", "")
        print(f"{call_sid}: {text}\n")

    print(">>> Check the calendar: both callers should have DIFFERENT time slots.")
    print(">>> If both show 'Next Monday at 9am' booked, the race condition fix failed.")


if __name__ == "__main__":
    test_invalid_email_rejected()
    test_invalid_name_rejected()
    test_invalid_dob_rejected()
    test_double_booking_race()