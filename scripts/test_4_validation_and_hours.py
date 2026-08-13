import sys, time
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

PAUSE = 8

def send(config, call_sid, message):
    result = receptionist_graph.invoke({"current_message": message, "call_sid": call_sid}, config=config)
    print(f"\nYou: {message}")
    print(f"Assistant: {result.get('response_text')}")
    print(f"[debug] booking_stage={result.get('booking_stage')} name={result.get('patient_name')} age={result.get('patient_age')} email={result.get('patient_email')}")
    time.sleep(PAUSE)
    return result

if __name__ == "__main__":
    # --- Validation: bad name, bad age, bad email ---
    config = {"configurable": {"thread_id": "t4a"}}
    print(f"Assistant: {greeting_node({})['response_text']}")
    send(config, "t4a", "I'd like to book an appointment")
    send(config, "t4a", "John")                              # invalid name
    send(config, "t4a", "My name is John Rivera, age 250")    # invalid age
    send(config, "t4a", "sorry im 45")
    send(config, "t4a", "not.an.email")                       # invalid email
    send(config, "t4a", "john.rivera@email.com")
    send(config, "t4a", "General checkup")
    send(config, "t4a", "In eight days at 3pm")
    send(config, "t4a", "yeah")   # tests casual confirmation word

    # --- Business hours: before open, after close, then valid ---
    config2 = {"configurable": {"thread_id": "t4b"}}
    print(f"\nAssistant: {greeting_node({})['response_text']}")
    send(config2, "t4b", "I'd like to book an appointment")
    send(config2, "t4b", "My name is System Test Hours, I'm 28")
    send(config2, "t4b", "hours.test@email.com")
    send(config2, "t4b", "Checkup")
    send(config2, "t4b", "Tomorrow at 7am")     # before opening
    send(config2, "t4b", "Tomorrow at 8pm")     # after closing
    result = send(config2, "t4b", "27 August at 10am")  # valid
    send(config2, "t4b", "yes")

    # --- Past date rejection ---
    config3 = {"configurable": {"thread_id": "t4c"}}
    print(f"\nAssistant: {greeting_node({})['response_text']}")
    send(config3, "t4c", "I'd like to book an appointment")
    send(config3, "t4c", "My name is System Test Past, I'm 30")
    send(config3, "t4c", "past.test@email.com")
    send(config3, "t4c", "Checkup")
    yesterday = (datetime.now() - timedelta(days=2)).strftime("%B %d")
    send(config3, "t4c", f"{yesterday} at 10am")   # should reject as past