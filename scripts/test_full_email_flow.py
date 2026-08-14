import sys
import time
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import TEST_PATIENT_EMAILS
from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

PAUSE = 8
CALL_SID = f"email-flow-test-{uuid.uuid4().hex[:8]}"  # unique every run, avoids stale state collisions


def send(config, call_sid, message):
    result = receptionist_graph.invoke({"current_message": message, "call_sid": call_sid}, config=config)
    print(f"\nYou: {message}")
    print(f"Assistant: {result.get('response_text')}")
    print(f"[debug] booking_stage={result.get('booking_stage')} rc_stage={result.get('rc_stage')} booking_id={result.get('booking_id')}")
    time.sleep(PAUSE)
    return result


if __name__ == "__main__":
    if not TEST_PATIENT_EMAILS:
        print("❌ No TEST_PATIENT_EMAIL_1 / TEST_PATIENT_EMAIL_2 set in .env — cannot test.")
        sys.exit(1)

    test_email = TEST_PATIENT_EMAILS[0]
    print(f"Using whitelisted test email: {test_email}")
    print(f"Using fresh call_sid: {CALL_SID}")

    config = {"configurable": {"thread_id": CALL_SID}}
    print(f"\nAssistant: {greeting_node({})['response_text']}")

    print("\n" + "="*70)
    print("STEP 1 — Book an appointment (should trigger: Resend clinic notification + Gmail patient confirmation)")
    print("="*70)
    send(config, CALL_SID, "I'd like to book an appointment")
    send(config, CALL_SID, "My name is Email Flow Test, I'm 29")
    send(config, CALL_SID, test_email)
    send(config, CALL_SID, "It's for a routine checkup")
    send(config, CALL_SID, "September 29th at 3:30pm")
    r1 = send(config, CALL_SID, "yes")
    booking_id = r1.get("booking_id")

    if not booking_id:
        print("\n❌ Booking failed, cannot continue to reschedule/cancel steps.")
        sys.exit(1)

    print(f"\n>>> Booked with ID: {booking_id}")

    print("\n" + "="*70)
    print("STEP 2 — Reschedule it (should trigger: Resend clinic notification + Gmail patient confirmation)")
    print("="*70)
    send(config, CALL_SID, "I need to reschedule my appointment")
    send(config, CALL_SID, f"My booking ID is {booking_id}")
    send(config, CALL_SID, "Yes that's correct")
    send(config, CALL_SID, "September 30th at 2pm")
    send(config, CALL_SID, "yes")

    print("\n" + "="*70)
    print("STEP 3 — Cancel it (should trigger: Resend clinic notification + Gmail patient confirmation)")
    print("="*70)
    send(config, CALL_SID, "I need to cancel my appointment")
    send(config, CALL_SID, f"My booking ID is {booking_id}")
    send(config, CALL_SID, "Yes that's the right one")
    send(config, CALL_SID, "yes, please cancel it")

    print("\n" + "="*70)
    print("DONE. Check console output above for [email] lines, and check:")
    print(f"  1. Your clinic notification inbox — should have 3 emails (booked, rescheduled, cancelled)")
    print(f"  2. {test_email} inbox — should have 3 emails (confirmed, rescheduled, cancelled)")
    print("="*70)