# scripts/debug_minimal_graph2.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.mongodb import MongoDBSaver

uri = os.environ["MONGODB_URI"]


class SimpleState(TypedDict):
    counter: int


def increment_node(state: SimpleState) -> dict:
    return {"counter": state.get("counter", 0) + 1}


if __name__ == "__main__":
    graph = StateGraph(SimpleState)
    graph.add_node("increment", increment_node)
    graph.set_entry_point("increment")
    graph.add_edge("increment", END)

    with MongoDBSaver.from_conn_string(uri) as checkpointer:
        compiled = graph.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "minimal-test-002"}}

        # First call: no prior state exists, so counter starts at 0 -> becomes 1
        result1 = compiled.invoke({}, config=config)
        print(f"First invoke result: {result1}")

        # Second call: pass an EMPTY input so nothing overwrites the loaded
        # checkpoint — the node should see the persisted counter=1 and make it 2
        result2 = compiled.invoke({}, config=config)
        print(f"Second invoke result: {result2}")
        print("(if counter went 1 -> 2, persistence works within this run)")