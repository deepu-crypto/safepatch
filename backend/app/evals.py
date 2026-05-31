import json
from pathlib import Path
from typing import Any

from app.retrieval import search_similar_chunks
from app.llm import analyze_issue_with_context_structured
from app.guardrails import run_guardrails


def load_eval_cases(file_path: str) -> list[dict[str, Any]]:
    """
    Loads synthetic eval cases from JSON.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Eval file does not exist: {file_path}")

    return json.loads(path.read_text(encoding="utf-8"))


def collect_text_for_keyword_check(finding) -> str:
    """
    Combines the important text fields from the structured finding.

    We use this to check whether expected root-cause keywords appear.
    """

    evidence_reasons = " ".join(item.reason for item in finding.evidence)

    combined_text = f"""
    {finding.root_cause}
    {finding.fix_plan}
    {finding.limitations}
    {evidence_reasons}
    """

    return combined_text.lower()


def score_keyword_match(expected_keywords: list[str], finding) -> dict:
    """
    Scores how many expected keywords appeared in the finding.

    This is not perfect, but it gives us a simple beginner-friendly eval signal.
    """

    combined_text = collect_text_for_keyword_check(finding)

    hits = []
    misses = []

    for keyword in expected_keywords:
        if keyword.lower() in combined_text:
            hits.append(keyword)
        else:
            misses.append(keyword)

    total = len(expected_keywords)
    score = len(hits) / total if total else 1.0

    return {
        "score": round(score, 2),
        "hits": hits,
        "misses": misses
    }


def score_single_case(case: dict[str, Any]) -> dict[str, Any]:
    """
    Runs the full guarded RAG workflow for one eval case and scores the result.
    """

    issue = case["issue"]

    chunks = search_similar_chunks(query=issue, top_k=3)

    finding = analyze_issue_with_context_structured(
        issue=issue,
        retrieved_chunks=chunks
    )

    guardrail_report = run_guardrails(
        finding=finding,
        retrieved_chunks=chunks
    )

    retrieved_files = [chunk["file_path"] for chunk in chunks]
    cited_files = [item.file_path for item in finding.evidence]

    expected_files = set(case["expected_files"])
    expected_issue_types = set(case["expected_issue_types"])

    retrieved_file_hit = any(file in expected_files for file in retrieved_files)
    cited_file_hit = any(file in expected_files for file in cited_files)

    issue_type_match = finding.issue_type in expected_issue_types

    approval_match = (
        finding.requires_human_approval
        == case["expected_requires_human_approval"]
    )

    guardrail_match = (
        guardrail_report.passed
        == case["expected_guardrail_passed"]
    )

    evidence_present = len(finding.evidence) > 0

    keyword_result = score_keyword_match(
        expected_keywords=case["expected_keywords"],
        finding=finding
    )

    keyword_match = keyword_result["score"] >= 0.50

    checks = {
        "retrieved_file_hit": retrieved_file_hit,
        "cited_file_hit": cited_file_hit,
        "issue_type_match": issue_type_match,
        "approval_match": approval_match,
        "guardrail_match": guardrail_match,
        "evidence_present": evidence_present,
        "keyword_match": keyword_match
    }

    passed_checks = sum(1 for value in checks.values() if value)
    total_checks = len(checks)
    case_score = passed_checks / total_checks

    return {
        "case_id": case["id"],
        "issue": issue,
        "score": round(case_score, 2),
        "passed": case_score >= 0.80,
        "checks": checks,
        "keyword_result": keyword_result,
        "expected": {
            "files": case["expected_files"],
            "issue_types": case["expected_issue_types"],
            "requires_human_approval": case["expected_requires_human_approval"],
            "guardrail_passed": case["expected_guardrail_passed"]
        },
        "actual": {
            "retrieved_files": retrieved_files,
            "cited_files": cited_files,
            "issue_type": finding.issue_type,
            "severity": finding.severity,
            "confidence": finding.confidence,
            "requires_human_approval": finding.requires_human_approval,
            "guardrail_passed": guardrail_report.passed,
            "guardrail_risk_level": guardrail_report.risk_level,
            "root_cause": finding.root_cause,
            "fix_plan": finding.fix_plan
        }
    }


def run_offline_evals(eval_file_path: str) -> dict[str, Any]:
    """
    Runs all eval cases and returns a summary.
    """

    cases = load_eval_cases(eval_file_path)

    results = []

    for case in cases:
        print(f"Running eval case: {case['id']}")
        result = score_single_case(case)
        results.append(result)

    total_cases = len(results)
    passed_cases = sum(1 for result in results if result["passed"])

    average_score = (
        sum(result["score"] for result in results) / total_cases
        if total_cases
        else 0
    )

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": total_cases - passed_cases,
        "pass_rate": round(passed_cases / total_cases, 2) if total_cases else 0,
        "average_score": round(average_score, 2),
        "results": results
    }
