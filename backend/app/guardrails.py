import re

from app.schemas import AgentFinding, GuardrailCheck, GuardrailReport


DANGEROUS_PATTERNS = [
    "rm -rf",
    "drop table",
    "delete database",
    "truncate table",
    "git push --force",
    "chmod 777",
    "curl http",
    "curl https",
    "disable auth",
    "bypass authentication",
    "hardcode password",
    "expose secret"
]


SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"(?i)api[_-]?key\s*[:=]\s*[A-Za-z0-9_\-]{12,}",
    r"(?i)password\s*[:=]\s*[A-Za-z0-9_\-]{8,}",
    r"(?i)secret\s*[:=]\s*[A-Za-z0-9_\-]{8,}"
]


def check_evidence_present(finding: AgentFinding) -> GuardrailCheck:
    """
    The agent must provide at least one evidence item.
    """

    if not finding.evidence:
        return GuardrailCheck(
            name="evidence_present",
            status="fail",
            message="The finding does not include any evidence."
        )

    return GuardrailCheck(
        name="evidence_present",
        status="pass",
        message="The finding includes evidence."
    )


def check_evidence_files_exist(
    finding: AgentFinding,
    retrieved_chunks: list[dict]
) -> GuardrailCheck:
    """
    The agent should only cite files that came from retrieved context.

    This prevents the model from inventing file names.
    """

    retrieved_files = {chunk["file_path"] for chunk in retrieved_chunks}
    cited_files = {item.file_path for item in finding.evidence}

    unknown_files = cited_files - retrieved_files

    if unknown_files:
        return GuardrailCheck(
            name="evidence_files_exist",
            status="fail",
            message=f"The finding cites files that were not retrieved: {sorted(unknown_files)}"
        )

    return GuardrailCheck(
        name="evidence_files_exist",
        status="pass",
        message="All cited evidence files exist in the retrieved context."
    )


def check_confidence_threshold(
    finding: AgentFinding,
    minimum_confidence: float = 0.60
) -> GuardrailCheck:
    """
    Low confidence should not fully block the answer,
    but it should warn us to be careful.
    """

    if finding.confidence < minimum_confidence:
        return GuardrailCheck(
            name="confidence_threshold",
            status="warning",
            message=(
                f"Confidence is low: {finding.confidence}. "
                f"Minimum expected confidence is {minimum_confidence}."
            )
        )

    return GuardrailCheck(
        name="confidence_threshold",
        status="pass",
        message=f"Confidence is acceptable: {finding.confidence}."
    )


def check_unsafe_fix_plan(finding: AgentFinding) -> GuardrailCheck:
    """
    Checks whether the fix plan contains risky operations.
    """

    fix_plan_lower = finding.fix_plan.lower()

    for pattern in DANGEROUS_PATTERNS:
        if pattern in fix_plan_lower:
            return GuardrailCheck(
                name="unsafe_fix_plan",
                status="fail",
                message=f"The fix plan contains a risky action: {pattern}"
            )

    return GuardrailCheck(
        name="unsafe_fix_plan",
        status="pass",
        message="No dangerous action was found in the fix plan."
    )


def check_secret_leakage(finding: AgentFinding) -> GuardrailCheck:
    """
    Checks if the LLM output appears to contain secrets.
    """

    output_text = finding.model_dump_json()

    for pattern in SECRET_PATTERNS:
        if re.search(pattern, output_text):
            return GuardrailCheck(
                name="secret_leakage",
                status="fail",
                message="The finding appears to contain a secret or credential."
            )

    return GuardrailCheck(
        name="secret_leakage",
        status="pass",
        message="No obvious secret leakage detected."
    )


def check_human_approval(finding: AgentFinding) -> GuardrailCheck:
    """
    Since this system suggests code changes, human approval should be required.
    """

    if not finding.requires_human_approval:
        return GuardrailCheck(
            name="human_approval_required",
            status="warning",
            message="The finding does not require human approval, but code changes should be reviewed."
        )

    return GuardrailCheck(
        name="human_approval_required",
        status="pass",
        message="Human approval is required before applying changes."
    )


def run_guardrails(
    finding: AgentFinding,
    retrieved_chunks: list[dict]
) -> GuardrailReport:
    """
    Runs all guardrail checks and returns a final safety decision.
    """

    checks = [
        check_evidence_present(finding),
        check_evidence_files_exist(finding, retrieved_chunks),
        check_confidence_threshold(finding),
        check_unsafe_fix_plan(finding),
        check_secret_leakage(finding),
        check_human_approval(finding),
    ]

    has_failure = any(check.status == "fail" for check in checks)
    has_warning = any(check.status == "warning" for check in checks)

    if has_failure:
        return GuardrailReport(
            passed=False,
            risk_level="high",
            checks=checks,
            blocked_reason="One or more guardrail checks failed."
        )

    if has_warning:
        return GuardrailReport(
            passed=True,
            risk_level="medium",
            checks=checks,
            blocked_reason=None
        )

    return GuardrailReport(
        passed=True,
        risk_level="low",
        checks=checks,
        blocked_reason=None
    )
