import sys

from app.retrieval import search_similar_chunks
from app.llm import analyze_issue_with_context


if __name__ == "__main__":
    if len(sys.argv) > 1:
        issue = " ".join(sys.argv[1:])
    else:
        issue = "Login API returns 500 when email is missing."

    print("Analyzing issue with RAG...")
    print(f"Issue: {issue}")
    print()

    print("Step 1: Retrieving relevant code chunks from pgvector...")
    chunks = search_similar_chunks(query=issue, top_k=3)

    if not chunks:
        print("No relevant chunks found. Did you run ingestion?")
        sys.exit(0)

    print(f"Retrieved {len(chunks)} chunks.")
    print()

    for index, chunk in enumerate(chunks, start=1):
        print(
            f"Chunk {index}: {chunk['file_path']} "
            f"lines {chunk['start_line']}-{chunk['end_line']} "
            f"score={chunk['similarity_score']}"
        )

    print()
    print("Step 2: Sending retrieved context to LLM...")
    print()

    analysis = analyze_issue_with_context(issue=issue, retrieved_chunks=chunks)

    print("-" * 80)
    print("AI RCA")
    print("-" * 80)
    print(analysis)
