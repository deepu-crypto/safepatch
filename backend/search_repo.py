import sys

from app.retrieval import search_similar_chunks


def print_result(chunk: dict, rank: int):
    """
    Pretty-prints one retrieved code chunk.
    """
    print("=" * 80)
    print(f"Rank: {rank}")
    print(f"File: {chunk['file_path']}")
    print(f"Lines: {chunk['start_line']}-{chunk['end_line']}")
    print(f"Similarity Score: {chunk['similarity_score']}")
    print(f"Distance: {chunk['distance']}")
    print("-" * 80)
    print(chunk["content"])
    print("=" * 80)
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Login API returns 500 when email is missing."

    print("Searching repo for relevant code chunks...")
    print(f"Query: {query}")
    print()

    chunks = search_similar_chunks(query=query, top_k=5)

    if not chunks:
        print("No chunks found. Did you run ingestion?")
        sys.exit(0)

    for index, chunk in enumerate(chunks, start=1):
        print_result(chunk, index)
