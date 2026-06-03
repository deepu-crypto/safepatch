import sys

from app.graph import build_safepatch_graph


if __name__ == "__main__":
    if len(sys.argv) > 1:
        issue = " ".join(sys.argv[1:])
    else:
        issue = "Login API returns 500 when email is missing."

    print("Running SafePatch LangGraph workflow with patch planning...")
    print(f"Issue: {issue}")
    print()

    graph = build_safepatch_graph()

    final_state = graph.invoke({
        "issue": issue
    })

    print()
    print("=" * 80)
    print("Retrieved Chunks")
    print("=" * 80)

    for index, chunk in enumerate(final_state["retrieved_chunks"], start=1):
        print(
            f"{index}. {chunk['file_path']} "
            f"lines {chunk['start_line']}-{chunk['end_line']} "
            f"score={chunk['similarity_score']}"
        )

    print()
    print("=" * 80)
    print("Structured Agent Finding")
    print("=" * 80)
    print(final_state["finding"].model_dump_json(indent=2))

    print()
    print("=" * 80)
    print("Guardrail Report")
    print("=" * 80)
    print(final_state["guardrail_report"].model_dump_json(indent=2))

    print()
    print("=" * 80)
    print("Human Approval Result")
    print("=" * 80)
    print(f"Approved: {final_state['human_approved']}")
    print(f"Notes: {final_state['human_approval_notes']}")

    print()
    print("=" * 80)
    print("Patch Plan")
    print("=" * 80)

    patch_plan = final_state.get("patch_plan")

    if patch_plan is None:
        print("No patch plan generated.")
    else:
        print(patch_plan.model_dump_json(indent=2))

    print()
    print("=" * 80)
    print("Final Decision")
    print("=" * 80)
    print(final_state["final_decision"])
