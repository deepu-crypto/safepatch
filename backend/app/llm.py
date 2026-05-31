import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path="backend/.env")

OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")

client = OpenAI()


def analyze_issue_with_context(issue: str, retrieved_chunks: list[dict]) -> str:
    """
    Sends the issue and retrieved code chunks to the LLM.

    The LLM should explain:
    - root cause
    - evidence
    - suggested fix
    - confidence
    """

    if not issue.strip():
        raise ValueError("Issue cannot be empty.")

    if not retrieved_chunks:
        raise ValueError("No retrieved chunks provided.")

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

    context_text = "\n".join(context_blocks)

    prompt = f"""
You are a senior backend engineer and AI code investigation assistant.

Your task is to analyze the issue using ONLY the provided code context.

Issue:
{issue}

Retrieved code context:
{context_text}

Instructions:
1. Identify the most likely root cause.
2. Cite evidence using file path and line numbers.
3. Suggest a safe fix.
4. Mention if the evidence is insufficient.
5. Do not invent files, functions, or behavior not shown in the context.
6.Do not touch .env file or docker-compose.yml file or requirements.txt or dockerfile files.

Return the answer in this format:

Root Cause:
...

Evidence:
- ...

Suggested Fix:
...

Confidence:
Low / Medium / High

Human Approval Needed:
Yes / No
"""

    response = client.responses.create(
        model=OPENAI_LLM_MODEL,
        input=prompt
    )

    return response.output_text
