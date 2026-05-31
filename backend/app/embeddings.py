import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path="backend/.env")

OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

client = OpenAI()


def generate_embedding(text: str) -> list[float]:
    """
    Converts text into an OpenAI embedding vector.

    Input:
        "Login API fails when email is missing"

    Output:
        [0.01, -0.23, 0.56, ...]

    We use OpenAI text-embedding-3-small.
    By default, this model returns a 1536-dimensional vector.
    """
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("Cannot generate embedding for empty text.")

    response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=cleaned_text,
        encoding_format="float"
    )

    return response.data[0].embedding
