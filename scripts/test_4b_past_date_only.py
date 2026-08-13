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
    config = {"configurable": {"thread_id": "t4b_past"}}
    print(f"Assistant: {greeting_node({})['response_text']}")

    send(config, "t4b_past", "I'd like to book an appointment")
    send(config, "t4b_past", "My name is System Test Yesterday, I'm 30")
    send(config, "t4b_past", "yesterday.test@email.com")
    send(config, "t4b_past", "Checkup")
    r = send(config, "t4b_past", "Yesterday at 10am")
    print(f"\n>>> Expected booking_stage=collecting (rejected as past), got: {r.get('booking_stage')}")