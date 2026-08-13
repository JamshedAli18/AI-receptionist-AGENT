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
    print(f"[debug] category={result.get('detected_category')} escalated={result.get('escalated')}")
    time.sleep(PAUSE)
    return result

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "t1"}}
    print(f"Assistant: {greeting_node({})['response_text']}")

    send(config, "t1", "Hi how are you")
    send(config, "t1", "What are your hours on Saturday?")
    send(config, "t1", "Do you accept Medicare?")
    send(config, "t1", "What's your cancellation fee?")
    send(config, "t1", "What should I bring to my first visit?")