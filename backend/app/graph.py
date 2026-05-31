from typing import Any
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from app.retrieval import search_similar_chunks
from app.llm import analyze_issue_with_context_structured
from app.guardrails import run_guardrails
from app.schemas import AgentFinding, GuardrailReport


class SafePatchState(TypedDict, total=False):
    """
    This is the shared state that moves through the LangGraph workflow.

    Each node reads from this state and returns updates to this state.
    """

    issue: str
    retrieved_chunks: list[dict[str, Any]]
    finding: AgentFinding
    guardrail_report: GuardrailReport
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


def final_decision_node(state: SafePatchState) -> dict:
    """
    Node 4:
    Converts the guardrail report into a final decision.
    """

    guardrail_report = state["guardrail_report"]

    if guardrail_report.passed:
        decision = "SAFE_TO_CONTINUE_TO_HUMAN_REVIEW"
    else:
        decision = "BLOCKED_BY_GUARDRAILS"

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
    graph.add_node("final_decision", final_decision_node)

    graph.add_edge(START, "retrieve_context")
    graph.add_edge("retrieve_context", "analyze_issue")
    graph.add_edge("analyze_issue", "run_guardrails")
    graph.add_edge("run_guardrails", "final_decision")
    graph.add_edge("final_decision", END)

    return graph.compile()
