from app.rag.retrieve import retrieve_context

if __name__ == "__main__":
    test_queries = [
        ("What happens if I miss my appointment?", "cancellation_policy"),
        ("Do you take Medicare?", "insurance_billing"),
        ("What should I bring to my first visit?", "new_patient"),
        ("Are you open on Saturday?", "hours"),
    ]

    for query, category in test_queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}  (category filter: {category})")
        print('='*60)
        results = retrieve_context(query, category=category)
        for i, r in enumerate(results, 1):
            print(f"\n--- chunk {i} (score: {r['score']:.3f}) ---\n{r['text'][:250]}...")