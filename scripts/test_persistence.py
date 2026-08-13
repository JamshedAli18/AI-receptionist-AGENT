import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

CALL_SID = "persistence-test-002"

if __name__ == "__main__":
    config = {"configurable": {"thread_id": CALL_SID}}
    greeting_node({})

    result = receptionist_graph.invoke(
        {"current_message": "What are your hours on Saturday?", "call_sid": CALL_SID},
        config=config,
    )
    print(f"Assistant: {result['response_text']}")
    print(f"[debug] category={result.get('detected_category')}")
    print(f"[debug] transcript length so far: {len(result.get('transcript', []))}")

    print("\n" + "="*60)
    print("Now CLOSE this terminal completely, open a NEW one, cd back")
    print("into the project, and run this exact script again unchanged.")
    print("="*60)
    print("\nIf persistence works: transcript length should be HIGHER on")
    print("the second run (4 instead of 2) — because the graph will load")
    print("the earlier turn from MongoDB and append this new one to it,")
    print("instead of starting a brand new empty transcript.")