# scripts/debug_checkpoints.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient

uri = os.environ["MONGODB_URI"]
client = MongoClient(uri)

print("=== All databases ===")
for db_name in client.list_database_names():
    print(f"  {db_name}")

print("\n=== Collections in each relevant database ===")
for db_name in client.list_database_names():
    if db_name in ("admin", "local", "config"):
        continue
    db = client[db_name]
    print(f"\n[{db_name}]")
    for coll_name in db.list_collection_names():
        count = db[coll_name].count_documents({})
        print(f"  {coll_name}: {count} documents")
        if "checkpoint" in coll_name.lower():
            sample = db[coll_name].find_one()
            print(f"    sample doc keys: {list(sample.keys()) if sample else 'none'}")