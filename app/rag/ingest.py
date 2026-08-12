from pathlib import Path
from app.config import co, get_index, EMBED_MODEL
from app.rag.chunking import build_chunks_for_file, BUSINESS_ID, CATEGORY_MAP


def find_project_root(marker: str = "pyproject.toml") -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / marker).exists():
            return parent
    raise FileNotFoundError(f"Could not find {marker} in any parent directory")


KB_DIR = find_project_root() / "data" / "kb"


def embed_texts(texts: list[str], input_type: str) -> list[list[float]]:
    resp = co.embed(texts=texts, model=EMBED_MODEL, input_type=input_type)
    return resp.embeddings


def clear_namespace(index):
    """Wipe the entire namespace before a full re-ingest, so stale or
    duplicate vectors from prior runs can never linger regardless of
    whether filter-based delete is supported on the current Pinecone plan."""
    try:
        index.delete(delete_all=True, namespace=BUSINESS_ID)
        print(f"Cleared namespace '{BUSINESS_ID}'")
    except Exception as e:
        # Namespace not existing yet on first-ever run throws — safe to ignore
        print(f"Namespace clear skipped (likely first run): {e}")


def ingest_all():
    index = get_index()
    pdf_files = sorted(KB_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {KB_DIR}")
        return

    clear_namespace(index)

    all_vectors = []
    for pdf_path in pdf_files:
        category = CATEGORY_MAP.get(pdf_path.name, "general")
        records = build_chunks_for_file(pdf_path)
        if not records:
            continue

        texts = [r["text"] for r in records]
        embeddings = embed_texts(texts, input_type="search_document")

        for record, vector in zip(records, embeddings):
            all_vectors.append({
                "id": record["id"],
                "values": vector,
                "metadata": {**record["metadata"], "text": record["text"]},
            })
        print(f"Embedded {len(records)} chunks from {pdf_path.name} -> category '{category}'")

    index.upsert(vectors=all_vectors, namespace=BUSINESS_ID)
    print(f"\nUpserted {len(all_vectors)} vectors into namespace '{BUSINESS_ID}'")


if __name__ == "__main__":
    ingest_all()