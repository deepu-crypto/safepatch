from typing import Any
from typing_extensions import TypedDict

# pyrefly: ignore [missing-import]
from langgraph.graph import StateGraph, START, END

from app.retrieval import search_similar_chunks
from app.llm import analyze_issue_with_context_structured
from app.guardrails import run_guardrails
from app.schemas import AgentFinding, GuardrailReport
from app.audit import log_event


class SafePatchState(TypedDict, total=False):
    """
    This is the shared state that moves through the LangGraph workflow.

    Each node reads from this state and returns updates to this state.
    """

    issue: str
    retrieved_chunks: list[dict[str, Any]]
    finding: AgentFinding
    guardrail_report: GuardrailReport
    human_approved: bool
    human_approval_notes: str
    final_decision: str


def retrieve_context_node(state: SafePatchState) -> dict:
    """
    Node 1:
    Takes the issue and retrieves relevant code chunks from pgvector.
    """

    issue = state["issue"]

    chunks = search_similar_chunks(
        query=issue,
        top_k=3
    )

    return {
        "retrieved_chunks": chunks
    }


def analyze_issue_node(state: SafePatchState) -> dict:
    """
    Node 2:
    Sends the issue and retrieved chunks to the LLM.
    The LLM returns a structured AgentFinding.
    """

    issue = state["issue"]
    chunks = state["retrieved_chunks"]

    finding = analyze_issue_with_context_structured(
        issue=issue,
        retrieved_chunks=chunks
    )

    return {
        "finding": finding
    }


def run_guardrails_node(state: SafePatchState) -> dict:
    """
    Node 3:
    Runs safety checks against the structured LLM finding.
    """

    finding = state["finding"]
    chunks = state["retrieved_chunks"]

    guardrail_report = run_guardrails(
        finding=finding,
        retrieved_chunks=chunks
    )

    return {
        "guardrail_report": guardrail_report
    }


def human_approval_node(state: SafePatchState) -> dict:
    """
    Node 4:
    Asks the human whether the agent should continue toward patch planning.

    For this beginner project, we use a simple terminal yes/no input.
    In a production system, this would usually be a UI approval screen,
    Slack approval, GitHub PR review, or ticket workflow.
    """

    issue = state["issue"]
    finding = state["finding"]
    guardrail_report = state["guardrail_report"]

    if not guardrail_report.passed:
        log_event(
            event_type="human_approval_skipped",
            payload={
                "issue": issue,
                "reason": "Guardrails failed before human approval.",
                "risk_level": guardrail_report.risk_level,
                "blocked_reason": guardrail_report.blocked_reason
            }
        )

        return {
            "human_approved": False,
            "human_approval_notes": "Skipped because guardrails failed."
        }

    print()
    print("=" * 80)
    print("Human Approval Checkpoint")
    print("=" * 80)
    print("The agent has passed guardrails and is requesting approval to continue.")
    print()
    print("Issue:")
    print(issue)
    print()
    print("Root Cause:")
    print(finding.root_cause)
    print()
    print("Fix Plan:")
    print(finding.fix_plan)
    print()
    print(f"Confidence: {finding.confidence}")
    print(f"Guardrail Risk Level: {guardrail_report.risk_level}")
    print()

    user_input = input("Approve continuing to patch planning? (yes/no): ").strip().lower()

    approved = user_input in ["yes", "y"]

    if approved:
        notes = "Human approved continuing to patch planning."
    else:
        notes = "Human rejected continuing to patch planning."

    log_event(
        event_type="human_approval",
        payload={
            "issue": issue,
            "approved": approved,
            "notes": notes,
            "risk_level": guardrail_report.risk_level,
            "confidence": finding.confidence,
            "issue_type": finding.issue_type,
            "severity": finding.severity
        }
    )

    return {
        "human_approved": approved,
        "human_approval_notes": notes
    }


def final_decision_node(state: SafePatchState) -> dict:
    """
    Node 5:
    Converts guardrail + human approval result into a final decision.
    """

    guardrail_report = state["guardrail_report"]
    human_approved = state.get("human_approved", False)

    if not guardrail_report.passed:
        decision = "BLOCKED_BY_GUARDRAILS"
    elif human_approved:
        decision = "APPROVED_FOR_PATCH_PLANNING"
    else:
        decision = "REJECTED_BY_HUMAN_REVIEW"

    return {
        "final_decision": decision
    }


def build_safepatch_graph():
    """
    Builds and compiles the SafePatch LangGraph workflow.
    """

    graph = StateGraph(SafePatchState)

    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_node("analyze_issue", analyze_issue_node)
    graph.add_node("run_guardrails", run_guardrails_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("final_decision", final_decision_node)

    graph.add_edge(START, "retrieve_context")
    graph.add_edge("retrieve_context", "analyze_issue")
    graph.add_edge("analyze_issue", "run_guardrails")
    graph.add_edge("run_guardrails", "human_approval")
    graph.add_edge("human_approval", "final_decision")
    graph.add_edge("final_decision", END)

    return graph.compile()
