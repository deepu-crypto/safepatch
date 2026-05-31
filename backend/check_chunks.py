# pyrefly: ignore [missing-import]
from sqlalchemy import text
from app.db import engine

if __name__ == "__main__":
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT id, file_path, start_line, end_line
            FROM code_chunks
            ORDER BY id;
        """))

        rows = result.fetchall()

        print(f"Found {len(rows)} chunks in database.")

        for row in rows:
            print(
                f"ID={row.id} | {row.file_path} | "
                f"lines {row.start_line}-{row.end_line}"
            )
