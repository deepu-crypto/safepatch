import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(dotenv_path="backend/.env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Check backend/.env file.")

engine = create_engine(DATABASE_URL)


def test_db_connection():
    """
    Simple function to test whether Python can connect to PostgreSQL.
    """
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        return result.fetchone()[0]


def test_pgvector_extension():
    """
    Checks whether pgvector extension is enabled.
    """
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        )
        row = result.fetchone()
        return row is not None


def create_tables():
    """
    Creates the table that stores code chunks and OpenAI embeddings.

    embedding vector(1536):
    We use 1536 because OpenAI text-embedding-3-small returns 1536-dimensional vectors by default.
    """
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        connection.execute(text("""
            DROP TABLE IF EXISTS code_chunks;
        """))

        connection.execute(text("""
            CREATE TABLE code_chunks (
                id SERIAL PRIMARY KEY,
                repo_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector(1536) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        connection.execute(text("""
            CREATE INDEX code_chunks_embedding_idx
            ON code_chunks
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))


def clear_code_chunks():
    """
    Deletes old chunks so we can re-ingest the repo cleanly while developing.
    """
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM code_chunks;"))
