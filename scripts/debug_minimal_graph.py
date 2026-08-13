# scripts/debug_minimal_graph.py
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

        config = {"configurable": {"thread_id": "minimal-test-001"}}

        result1 = compiled.invoke({"counter": 0}, config=config)
        print(f"First invoke result: {result1}")

        result2 = compiled.invoke({"counter": 0}, config=config)
        print(f"Second invoke result: {result2}")
        print("(if counter went 1 -> 2, persistence works; if it's 1 -> 1, it doesn't)")

    print("\nChecking MongoDB for checkpoint collections...")
    from pymongo import MongoClient
    client = MongoClient(uri)
    for db_name in client.list_database_names():
        if db_name in ("admin", "local", "config", "sample_mflix"):
            continue
        db = client[db_name]
        for coll_name in db.list_collection_names():
            print(f"  {db_name}.{coll_name}: {db[coll_name].count_documents({})} documents")