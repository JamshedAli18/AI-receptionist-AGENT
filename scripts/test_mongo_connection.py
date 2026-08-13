# scripts/test_mongo_connection.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient

uri = os.environ["MONGODB_URI"]

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("✅ Connected successfully to MongoDB Atlas.")

    db = client["voice_receptionist"]
    print(f"Using database: {db.name}")

    # Write and read back a test document to confirm read/write access works
    test_collection = db["connection_test"]
    result = test_collection.insert_one({"status": "test", "message": "connection verified"})
    print(f"✅ Inserted test document with id: {result.inserted_id}")

    found = test_collection.find_one({"_id": result.inserted_id})
    print(f"✅ Read back: {found}")

    test_collection.delete_one({"_id": result.inserted_id})
    print("✅ Cleaned up test document.")

except Exception as e:
    print(f"❌ Connection failed: {e}")