from pathlib import Path
from app.config import co, get_index, EMBED_MODEL
from app.rag.chunking import build_chunks_for_file, BUSINESS_ID, CATEGORY_MAP


def find_project_root(marker: str = "pyproject.toml") -> Path:
    """Walk up from this file until we find the project root (has pyproject.toml)."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / marker).exists():
            return parent
    raise FileNotFoundError(f"Could not find {marker} in any parent directory")


KB_DIR = find_project_root() / "data" / "kb"


def embed_texts(texts: list[str], input_type: str) -> list[list[float]]:
    """input_type: 'search_document' when ingesting, 'search_query' when retrieving."""
    resp = co.embed(texts=texts, model=EMBED_MODEL, input_type=input_type)
    return resp.embeddings


def ingest_all():
    index = get_index()
    pdf_files = sorted(KB_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {KB_DIR}")
        return

    all_vectors = []
    for pdf_path in pdf_files:
        category = CATEGORY_MAP.get(pdf_path.name, "general")

        index.delete(filter={"category": {"$eq": category}}, namespace=BUSINESS_ID)

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