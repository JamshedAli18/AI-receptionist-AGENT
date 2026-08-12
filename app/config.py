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

# Embedding + rerank models (Cohere)
EMBED_MODEL = "embed-english-v3.0"
EMBED_DIM = 1024
RERANK_MODEL = "rerank-english-v3.0"

# Two Groq models, split by task
LLM_MODEL_FAST = "llama-3.1-8b-instant"        # classification, entity extraction
LLM_MODEL_QUALITY = "llama-3.3-70b-versatile"   # RAG answer generation, confirmations

CLINIC_TIMEZONE = os.environ.get("CLINIC_TIMEZONE", "America/New_York")

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