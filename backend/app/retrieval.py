# pyrefly: ignore [missing-import]
from sqlalchemy import text

from app.db import engine
from app.embeddings import generate_embedding


def vector_to_pgvector(vector: list[float]) -> str:
    """
    Converts a Python list into pgvector format.

    Python list:
    [0.1, 0.2, 0.3]

    pgvector format:
    '[0.1,0.2,0.3]'
    """
    return "[" + ",".join(str(value) for value in vector) + "]"


def search_similar_chunks(
    query: str,
    repo_name: str = "sample_repo",
    top_k: int = 5
) -> list[dict]:
    """
    Searches pgvector for code chunks that are semantically similar to the query.

    Example query:
        "Login API returns 500 when email is missing"

    Returns:
        A list of the most relevant code chunks.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    query_embedding = generate_embedding(query)
    query_embedding_str = vector_to_pgvector(query_embedding)

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    repo_name,
                    file_path,
                    start_line,
                    end_line,
                    content,
                    embedding <=> CAST(:query_embedding AS vector) AS distance
                FROM code_chunks
                WHERE repo_name = :repo_name
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT :top_k;
            """),
            {
                "query_embedding": query_embedding_str,
                "repo_name": repo_name,
                "top_k": top_k
            }
        )

        rows = result.fetchall()

    chunks = []

    for row in rows:
        distance = float(row.distance)
        similarity_score = 1 - distance

        chunks.append({
            "id": row.id,
            "repo_name": row.repo_name,
            "file_path": row.file_path,
            "start_line": row.start_line,
            "end_line": row.end_line,
            "content": row.content,
            "distance": round(distance, 4),
            "similarity_score": round(similarity_score, 4)
        })

    return chunks
