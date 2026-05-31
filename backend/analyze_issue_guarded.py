import sys

from app.retrieval import search_similar_chunks
from app.llm import analyze_issue_with_context_structured
from app.guardrails import run_guardrails


if __name__ == "__main__":
    if len(sys.argv) > 1:
        issue = " ".join(sys.argv[1:])
    else:
        issue = "Login API returns 500 when email is missing."

    print("Running guarded RAG analysis...")
    print(f"Issue: {issue}")
    print()

    print("Step 1: Retrieving relevant code chunks from pgvector...")
    chunks = search_similar_chunks(query=issue, top_k=3)

    if not chunks:
        print("No relevant chunks found. Did you run ingestion?")
        sys.exit(0)

    for index, chunk in enumerate(chunks, start=1):
        print(
            f"Chunk {index}: {chunk['file_path']} "
            f"lines {chunk['start_line']}-{chunk['end_line']} "
            f"score={chunk['similarity_score']}"
        )

    print()
    print("Step 2: Generating structured LLM finding...")
    finding = analyze_issue_with_context_structured(
        issue=issue,
        retrieved_chunks=chunks
    )

    print()
    print("=" * 80)
    print("Structured Agent Finding")
    print("=" * 80)
    print(finding.model_dump_json(indent=2))

    print()
    print("Step 3: Running safety guardrails...")
    guardrail_report = run_guardrails(
        finding=finding,
        retrieved_chunks=chunks
    )

    print()
    print("=" * 80)
    print("Guardrail Report")
    print("=" * 80)
    print(guardrail_report.model_dump_json(indent=2))

    print()
    if guardrail_report.passed:
        print("Final Decision: SAFE TO CONTINUE TO HUMAN REVIEW")
    else:
        print("Final Decision: BLOCKED")
        print(f"Reason: {guardrail_report.blocked_reason}")
