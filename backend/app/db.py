import os
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
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
