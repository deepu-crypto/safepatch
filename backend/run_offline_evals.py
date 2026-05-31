import json
from datetime import datetime
from pathlib import Path

from app.evals import run_offline_evals


if __name__ == "__main__":
    eval_file_path = "eval_cases/offline_eval_cases.json"

    print("Running offline eval suite...")
    print(f"Eval file: {eval_file_path}")
    print()

    summary = run_offline_evals(eval_file_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(f"eval_results/offline_eval_results_{timestamp}.json")

    output_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8"
    )

    print()
    print("=" * 80)
    print("Offline Eval Summary")
    print("=" * 80)
    print(f"Total cases: {summary['total_cases']}")
    print(f"Passed cases: {summary['passed_cases']}")
    print(f"Failed cases: {summary['failed_cases']}")
    print(f"Pass rate: {summary['pass_rate']}")
    print(f"Average score: {summary['average_score']}")
    print()
    print(f"Saved full results to: {output_path}")

    print()
    print("=" * 80)
    print("Case Results")
    print("=" * 80)

    for result in summary["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status} | {result['case_id']} | score={result['score']}")

        for check_name, check_value in result["checks"].items():
            check_status = "OK" if check_value else "MISS"
            print(f"  - {check_status}: {check_name}")

        print()
