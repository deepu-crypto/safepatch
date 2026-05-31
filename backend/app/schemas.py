from typing import Literal
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """
    One piece of proof supporting the agent's answer.
    """

    file_path: str = Field(description="The file where the evidence was found.")
    start_line: int = Field(description="The starting line number for the evidence.")
    end_line: int = Field(description="The ending line number for the evidence.")
    reason: str = Field(description="Why this code supports the root cause.")


class AgentFinding(BaseModel):
    """
    Final structured output returned by the LLM.

    This becomes the contract between the LLM and our backend.
    """

    issue_type: Literal[
        "bug",
        "security",
        "test_failure",
        "dependency",
        "unknown"
    ] = Field(description="The type of issue being investigated.")

    severity: Literal[
        "low",
        "medium",
        "high",
        "critical"
    ] = Field(description="The estimated severity of the issue.")

    root_cause: str = Field(description="The most likely root cause based only on retrieved context.")

    evidence: list[Evidence] = Field(description="Evidence from retrieved code chunks.")

    fix_plan: str = Field(description="A safe, high-level fix plan.")

    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence score between 0 and 1."
    )

    requires_human_approval: bool = Field(
        description="Whether a human should approve before applying changes."
    )

    limitations: str = Field(
        description="Mention what context is missing or uncertain."
    )


class GuardrailCheck(BaseModel):
    """
    One safety check result.
    """

    name: str
    status: Literal["pass", "warning", "fail"]
    message: str


class GuardrailReport(BaseModel):
    """
    Final guardrail decision.

    If passed is false, the agent output should not be trusted for patch generation.
    """

    passed: bool
    risk_level: Literal["low", "medium", "high"]
    checks: list[GuardrailCheck]
    blocked_reason: str | None = None
