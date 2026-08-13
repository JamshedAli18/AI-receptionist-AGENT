# scripts/debug_checkpointer_direct.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
from dotenv import load_dotenv
load_dotenv()

from langgraph.checkpoint.mongodb import MongoDBSaver

uri = os.environ["MONGODB_URI"]

print("Testing MongoDBSaver directly...")

with MongoDBSaver.from_conn_string(uri) as checkpointer:
    print(f"Checkpointer created: {checkpointer}")

    config = {"configurable": {"thread_id": "direct-test-001"}}

    # Try writing a checkpoint manually
    from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
    import uuid

    test_checkpoint = Checkpoint(
        v=1,
        id=str(uuid.uuid4()),
        ts="2026-01-01T00:00:00+00:00",
        channel_values={"test_key": "test_value"},
        channel_versions={},
        versions_seen={},
    )
    test_metadata = CheckpointMetadata(source="input", step=0, writes=None, parents={})

    checkpointer.put(config, test_checkpoint, test_metadata, {})
    print("Wrote a test checkpoint.")

    loaded = checkpointer.get(config)
    print(f"Loaded back: {loaded}")

print("\nNow checking MongoDB directly for what got created...")
from pymongo import MongoClient
client = MongoClient(uri)
for db_name in client.list_database_names():
    if db_name in ("admin", "local", "config", "sample_mflix"):
        continue
    db = client[db_name]
    for coll_name in db.list_collection_names():
        print(f"  {db_name}.{coll_name}: {db[coll_name].count_documents({})} documents")