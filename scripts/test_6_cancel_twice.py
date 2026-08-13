import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

PAUSE = 8

def send(config, call_sid, message):
    result = receptionist_graph.invoke({"current_message": message, "call_sid": call_sid}, config=config)
    print(f"\nYou: {message}")
    print(f"Assistant: {result.get('response_text')}")
    print(f"[debug] rc_stage={result.get('rc_stage')} escalated={result.get('escalated')} booking_id={result.get('booking_id')}")
    time.sleep(PAUSE)
    return result

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "t6"}}
    print(f"Assistant: {greeting_node({})['response_text']}")

    print("\n--- First booking ---")
    send(config, "t6", "I'd like to book an appointment")
    send(config, "t6", "My name is System Test Cancel One, I'm 27")
    send(config, "t6", "cancelone.test@email.com")
    send(config, "t6", "Sick visit")
    send(config, "t6", "7 September at 1pm")
    r1 = send(config, "t6", "yes")
    booking_id_1 = r1.get("booking_id")

    print("\n--- First cancel ---")
    send(config, "t6", "I need to cancel my appointment")
    send(config, "t6", f"My booking ID is {booking_id_1}")
    send(config, "t6", "Yes that's the right one")
    send(config, "t6", "yes, please cancel it")

    print("\n--- Second booking (SAME session) ---")
    send(config, "t6", "I'd like to book another appointment")
    send(config, "t6", "My name is System Test Cancel Two, I'm 31")
    send(config, "t6", "canceltwo.test@email.com")
    send(config, "t6", "Follow-up visit")
    send(config, "t6", "7 September at 4pm")
    r2 = send(config, "t6", "yes")
    booking_id_2 = r2.get("booking_id")

    print("\n--- Second cancel attempt — THIS IS THE BUG FIX TEST ---")
    r3 = send(config, "t6", "I need to cancel my appointment")
    print(f">>> Expected rc_stage=lookup, got: {r3.get('rc_stage')}")

    if r3.get("rc_stage") == "lookup":
        send(config, "t6", f"My booking ID is {booking_id_2}")
        send(config, "t6", "yes")
        send(config, "t6", "yes")