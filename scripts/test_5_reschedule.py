import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

PAUSE = 8
BOOKING_ID = "BP515021"   # <-- update this before running

def send(config, call_sid, message):
    result = receptionist_graph.invoke({"current_message": message, "call_sid": call_sid}, config=config)
    print(f"\nYou: {message}")
    print(f"Assistant: {result.get('response_text')}")
    print(f"[debug] rc_stage={result.get('rc_stage')} escalated={result.get('escalated')}")
    time.sleep(PAUSE)
    return result

if __name__ == "__main__":
    if BOOKING_ID == "PASTE_ID_FROM_TEST_3_HERE":
        print("Set BOOKING_ID at the top of this file to the ID from test_3 first.")
        sys.exit(1)

    config = {"configurable": {"thread_id": "t5"}}
    print(f"Assistant: {greeting_node({})['response_text']}")

    send(config, "t5", "I need to reschedule my appointment")
    send(config, "t5", f"My booking ID is {BOOKING_ID}")
    send(config, "t5", "Yes that's correct")
    send(config, "t5", "Can we move it to next Monday at 2pm")
    send(config, "t5", "yeah")