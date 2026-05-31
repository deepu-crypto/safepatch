from app.db import test_db_connection, test_pgvector_extension

if __name__ == "__main__":
    print("Testing database connection...")

    version = test_db_connection()
    print("Connected to PostgreSQL:")
    print(version)

    print("\nChecking pgvector extension...")
    is_vector_enabled = test_pgvector_extension()

    if is_vector_enabled:
        print("pgvector is enabled.")
    else:
        print("pgvector is NOT enabled.")
