import os
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient

_client = None


def get_db():
    global _client
    if _client is None:
        uri = os.environ["MONGODB_URI"]
        _client = MongoClient(uri)
    return _client["voice_receptionist"]


def get_patients_collection():
    return get_db()["patients"]


def get_appointments_collection():
    return get_db()["appointments"]


def get_escalations_collection():
    return get_db()["escalations"]