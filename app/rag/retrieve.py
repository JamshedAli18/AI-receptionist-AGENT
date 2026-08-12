import time
from cohere.errors.too_many_requests_error import TooManyRequestsError
from app.config import co, get_index, EMBED_MODEL, RERANK_MODEL
from app.rag.chunking import BUSINESS_ID


def _rerank_with_retry(query, candidates, top_n, max_retries=3):
    if not candidates:
        return []
    for attempt in range(max_retries):
        try:
            reranked = co.rerank(
                query=query, documents=candidates, model=RERANK_MODEL,
                top_n=min(top_n, len(candidates)),
            )
            return [{"text": candidates[r.index], "score": r.relevance_score} for r in reranked.results]
        except TooManyRequestsError:
            if attempt == max_retries - 1:
                raise
            wait = 20 * (attempt + 1)   # 20s, 40s — enough to clear into the next minute window
            print(f"[retrieve] rate limited, retrying in {wait}s...")
            time.sleep(wait)

def _search(query_embedding, category, top_k, index):
    metadata_filter = {"active": {"$eq": True}}
    if category:
        metadata_filter["category"] = {"$eq": category}

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace=BUSINESS_ID,
        filter=metadata_filter,
        include_metadata=True,
    )

    seen_ids = set()
    candidates = []
    for match in results["matches"]:
        match_id = match.get("id")
        text = match["metadata"]["text"]
        dedupe_key = match_id or text
        if dedupe_key in seen_ids:
            continue
        seen_ids.add(dedupe_key)
        candidates.append(text)
    return candidates


def retrieve_context(
    query: str,
    category: str | None = None,
    top_k: int = 8,
    top_n: int = 4,
    fallback_threshold: float = 0.35,
) -> list[dict]:
    index = get_index()
    query_embedding = co.embed(
        texts=[query], model=EMBED_MODEL, input_type="search_query"
    ).embeddings[0]

    primary_candidates = _search(query_embedding, category, top_k, index)
    primary = _rerank_with_retry(query, primary_candidates, top_n)
    primary_score = primary[0]["score"] if primary else 0.0

    if category and primary_score < fallback_threshold:
        fallback_candidates = _search(query_embedding, None, top_k, index)
        fallback = _rerank_with_retry(query, fallback_candidates, top_n)
        fallback_score = fallback[0]["score"] if fallback else 0.0
        if fallback_score > primary_score:
            return fallback

    return primary