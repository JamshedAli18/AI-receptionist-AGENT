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
    print(f"[debug] booking_stage={result.get('booking_stage')} booking_id={result.get('booking_id')}")
    time.sleep(PAUSE)
    return result

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "t3"}}
    print(f"Assistant: {greeting_node({})['response_text']}")

    send(config, "t3", "I'd like to book an appointment")
    send(config, "t3", "My name is System Test Alpha, I'm 30")
    send(config, "t3", "systemtest.alpha@email.com")
    send(config, "t3", "Routine checkup")
    send(config, "t3", "September 15th at 1pm")
    result = send(config, "t3", "yeah")

    print(f"\n>>> SAVE THIS BOOKING ID for test 5 (reschedule): {result.get('booking_id')}")