"""Runs the plan-draft eval against the real model and prints accuracy per field, tokens, latency and cost.

    python -m evals.run_eval                       # all cases
    python -m evals.run_eval --ids asado-sabado    # just those
    python -m evals.run_eval --min-pass 0.9        # exit 1 below 90% (for CI or a pre-merge check)

Needs BEDROCK_MODEL_ID and AWS credentials (the same settings the app uses), and it spends real tokens: about a
cent or two per full run with a small model. Run it whenever the prompt, the tool schema or the model changes, and
compare the numbers with the run before.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app import plan_draft
from app.config import settings
from evals.scoring import CaseScore, score, summarize

HERE = Path(__file__).parent


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", type=Path, default=HERE / "cases.jsonl")
    parser.add_argument("--ids", help="comma-separated case ids to run")
    parser.add_argument("--min-pass", type=float, default=0.0, help="exit 1 if the pass rate is below this (0-1)")
    parser.add_argument("--price-in", type=float, default=1.0, help="USD per million input tokens (check your model's price)")
    parser.add_argument("--price-out", type=float, default=5.0, help="USD per million output tokens")
    parser.add_argument("--report", type=Path, default=HERE / "results" / "last_run.json")
    args = parser.parse_args()

    if not settings.bedrock_model_id:
        print("BEDROCK_MODEL_ID is empty: set it (and the AWS credentials) in .env first.", file=sys.stderr)
        return 2

    cases = load_cases(args.cases)
    if args.ids:
        wanted = set(args.ids.split(","))
        cases = [c for c in cases if c["id"] in wanted]

    tz = ZoneInfo(plan_draft.DEFAULT_TZ)
    scores: list[CaseScore] = []
    tokens_in = tokens_out = latency = 0
    print(f"model {settings.bedrock_model_id} · {len(cases)} cases\n")
    for case in cases:
        now = datetime.fromisoformat(case["now"]).replace(tzinfo=tz)
        try:
            draft, usage = plan_draft.generate(case["text"], now=now)
        except Exception as exc:  # a failed call is a failed case, not a crashed run
            result = CaseScore(case["id"], error=f"{type(exc).__name__}: {exc}")
        else:
            result = score(case, draft)
            result.raw = usage.arguments
            tokens_in += usage.input_tokens
            tokens_out += usage.output_tokens
            latency += usage.latency_ms
        scores.append(result)
        print(f"{'PASS' if result.passed else 'FAIL'}  {case['id']}")
        if result.error:
            print(f"      error: {result.error}")
        for name, detail in result.details.items():
            print(f"      {name}: {detail}")
        if not result.passed and result.raw is not None:
            print(f"      model said: {json.dumps(result.raw, ensure_ascii=False)}")

    summary = summarize(scores)
    cost = tokens_in / 1e6 * args.price_in + tokens_out / 1e6 * args.price_out
    print(f"\n{summary['passed']}/{summary['cases']} cases pass ({summary['pass_rate']:.0%}), {summary['errors']} errors")
    for name, (accuracy, count) in summary["per_field"].items():
        print(f"  {name:<18} {accuracy:>5.0%}  ({count} cases)")
    answered = max(summary["cases"] - summary["errors"], 1)
    print(f"\ntokens in/out {tokens_in}/{tokens_out} · avg latency {latency // answered} ms · est. cost ${cost:.4f}")

    args.report.parent.mkdir(exist_ok=True)
    args.report.write_text(
        json.dumps(
            {
                "model": settings.bedrock_model_id,
                "summary": summary,
                "tokens": {"in": tokens_in, "out": tokens_out},
                "estimated_cost_usd": round(cost, 6),
                "failures": [
                    {"id": s.case_id, "error": s.error, "details": s.details, "model_said": s.raw}
                    for s in scores
                    if not s.passed
                ],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return 0 if summary["pass_rate"] >= args.min_pass else 1


if __name__ == "__main__":
    sys.exit(main())
