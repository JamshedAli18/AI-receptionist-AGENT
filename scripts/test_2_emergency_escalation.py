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
    print(f"[debug] is_emergency={result.get('is_emergency')} escalated={result.get('escalated')}")
    time.sleep(PAUSE)
    return result

if __name__ == "__main__":
    config1 = {"configurable": {"thread_id": "t2a"}}
    print(f"Assistant: {greeting_node({})['response_text']}")
    send(config1, "t2a", "I'm having really bad chest pain")

    config2 = {"configurable": {"thread_id": "t2b"}}
    print(f"\nAssistant: {greeting_node({})['response_text']}")
    send(config2, "t2b", "I want to book an appointment but I've had chest pain")

    config3 = {"configurable": {"thread_id": "t2c"}}
    print(f"\nAssistant: {greeting_node({})['response_text']}")
    send(config3, "t2c", "Do you have a pediatric dentist on staff?")