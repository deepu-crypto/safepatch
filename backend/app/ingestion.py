from pathlib import Path
# pyrefly: ignore [missing-import]
from sqlalchemy import text

from app.db import engine, create_tables, clear_code_chunks
from app.embeddings import generate_embedding


def read_python_files(repo_path: str) -> list[Path]:
    """
    Finds all Python files inside the sample repo.

    We ignore hidden folders and cache folders.
    """
    root = Path(repo_path)

    if not root.exists():
        raise FileNotFoundError(f"Repo path does not exist: {repo_path}")

    python_files = []

    for file_path in root.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue

        python_files.append(file_path)

    return python_files


def chunk_file(file_path: Path, chunk_size: int = 40, overlap: int = 10) -> list[dict]:
    """
    Splits a file into overlapping line-based chunks.

    Example:
    chunk_size=40, overlap=10

    Chunk 1: lines 1-40
    Chunk 2: lines 31-70
    Chunk 3: lines 61-100
    """
    lines = file_path.read_text(encoding="utf-8").splitlines()

    chunks = []
    start = 0

    while start < len(lines):
        end = min(start + chunk_size, len(lines))
        chunk_lines = lines[start:end]
        content = "\n".join(chunk_lines)

        if content.strip():
            chunks.append({
                "start_line": start + 1,
                "end_line": end,
                "content": content
            })

        if end == len(lines):
            break

        start = end - overlap

    return chunks


def vector_to_pgvector(vector: list[float]) -> str:
    """
    Converts Python list into pgvector string format.

    Python list:
    [0.1, 0.2, 0.3]

    pgvector format:
    '[0.1,0.2,0.3]'
    """
    return "[" + ",".join(str(value) for value in vector) + "]"


def store_chunk(
    repo_name: str,
    file_path: str,
    start_line: int,
    end_line: int,
    content: str,
    embedding: list[float]
):
    """
    Stores one code chunk into PostgreSQL.
    """
    embedding_str = vector_to_pgvector(embedding)

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO code_chunks (
                    repo_name,
                    file_path,
                    start_line,
                    end_line,
                    content,
                    embedding
                )
                VALUES (
                    :repo_name,
                    :file_path,
                    :start_line,
                    :end_line,
                    :content,
                    :embedding
                )
            """),
            {
                "repo_name": repo_name,
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
                "embedding": embedding_str
            }
        )


def ingest_repo(repo_path: str, repo_name: str = "sample_repo"):
    """
    Main ingestion function.

    This prepares the database and stores all Python code chunks.
    """
    print("Creating database tables...")
    create_tables()

    print("Clearing old code chunks...")
    clear_code_chunks()

    print(f"Reading Python files from: {repo_path}")
    python_files = read_python_files(repo_path)

    print(f"Found {len(python_files)} Python files.")

    total_chunks = 0

    for file_path in python_files:
        relative_path = str(file_path.relative_to(Path(repo_path)))

        print(f"Chunking file: {relative_path}")
        chunks = chunk_file(file_path)

        for chunk in chunks:
            print(
                f"Embedding chunk: {relative_path} "
                f"lines {chunk['start_line']}-{chunk['end_line']}"
            )

            embedding = generate_embedding(chunk["content"])

            store_chunk(
                repo_name=repo_name,
                file_path=relative_path,
                start_line=chunk["start_line"],
                end_line=chunk["end_line"],
                content=chunk["content"],
                embedding=embedding
            )

            total_chunks += 1

    print(f"Ingestion complete. Stored {total_chunks} chunks.")
