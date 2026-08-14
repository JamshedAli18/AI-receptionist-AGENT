import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import cohere
from groq import Groq

load_dotenv()

PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
COHERE_API_KEY = os.environ["COHERE_API_KEY"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "brightpath-clinic-kb")

EMBED_MODEL = "embed-english-v3.0"
EMBED_DIM = 1024
RERANK_MODEL = "rerank-english-v3.0"

LLM_MODEL_FAST = "llama-3.1-8b-instant"
LLM_MODEL_QUALITY = "llama-3.3-70b-versatile"

CLINIC_TIMEZONE = os.environ.get("CLINIC_TIMEZONE", "America/New_York")

MONGODB_URI = os.environ["MONGODB_URI"]

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
CLINIC_NOTIFICATION_EMAILS = [
    e for e in [
        os.environ.get("CLINIC_NOTIFICATION_EMAIL_1"),
        os.environ.get("CLINIC_NOTIFICATION_EMAIL_2"),
    ] if e
]

GMAIL_SMTP_USER = os.environ.get("GMAIL_SMTP_USER")
GMAIL_SMTP_APP_PASSWORD = os.environ.get("GMAIL_SMTP_APP_PASSWORD")

SIGNALWIRE_PROJECT_ID = os.environ.get("SIGNALWIRE_PROJECT_ID")
SIGNALWIRE_API_TOKEN = os.environ.get("SIGNALWIRE_API_TOKEN")
SIGNALWIRE_SPACE_URL = os.environ.get("SIGNALWIRE_SPACE_URL")
SIGNALWIRE_PHONE_NUMBER = os.environ.get("SIGNALWIRE_PHONE_NUMBER")

TEST_PATIENT_EMAILS = [
    e.lower() for e in [
        os.environ.get("TEST_PATIENT_EMAIL_1"),
        os.environ.get("TEST_PATIENT_EMAIL_2"),
    ] if e
]

co = cohere.Client(COHERE_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)


def get_index():
    existing = [i.name for i in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(PINECONE_INDEX_NAME)