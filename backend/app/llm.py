import os
from dotenv import load_dotenv
from openai import OpenAI

from app.schemas import AgentFinding

load_dotenv(dotenv_path="backend/.env")

OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")

client = OpenAI()


def build_context_text(retrieved_chunks: list[dict]) -> str:
    """
    Converts retrieved chunks into a readable context block for the LLM.
    """

    context_blocks = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"""
[Context Chunk {index}]
File: {chunk['file_path']}
Lines: {chunk['start_line']}-{chunk['end_line']}
Similarity Score: {chunk['similarity_score']}

Code:
{chunk['content']}
"""
        )

    return "\n".join(context_blocks)


def analyze_issue_with_context(issue: str, retrieved_chunks: list[dict]) -> str:
    """
    Older free-text analysis function.

    Kept for comparison, but our production-style flow should use
    analyze_issue_with_context_structured().
    """

    structured_result = analyze_issue_with_context_structured(issue, retrieved_chunks)
    return structured_result.model_dump_json(indent=2)


def analyze_issue_with_context_structured(
    issue: str,
    retrieved_chunks: list[dict]
) -> AgentFinding:
    """
    Sends the issue and retrieved chunks to the LLM.

    Instead of free-form text, this forces the LLM to return an AgentFinding object.
    """

    if not issue.strip():
        raise ValueError("Issue cannot be empty.")

    if not retrieved_chunks:
        raise ValueError("No retrieved chunks provided.")

    context_text = build_context_text(retrieved_chunks)

    system_message = """
You are a senior backend engineer and AI code investigation assistant.

You must analyze issues using ONLY the provided retrieved code context.

Rules:
- Do not invent files, functions, line numbers, or behavior.
- Every root cause must be supported by evidence.
- Evidence must reference file paths and line ranges from the provided context.
- If the context is not enough, say that in limitations.
- Prefer requiring human approval for code changes.
- Do not touch .env file or docker-compose.yml file or requirements.txt or dockerfile files.
"""

    user_message = f"""
Issue:
{issue}

Retrieved code context:
{context_text}

Return a structured investigation result.
"""

    response = client.responses.parse(
        model=OPENAI_LLM_MODEL,
        input=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        text_format=AgentFinding
    )

    return response.output_parsed
