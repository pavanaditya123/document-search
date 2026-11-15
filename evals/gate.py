"""
Quality gate for eval runs.

A run passes only if every metric is
  1. at or above its floor in thresholds.json, and
  2. not more than MAX_DROP below the last accepted run (baseline.json).

Rule 2 catches the slow kind of regression: a prompt or chunking change that
takes faithfulness from 0.95 to 0.88 still clears a 0.85 floor, but it is
a real drop and someone should look at it before it ships.

    python -m evals.gate evals/reports/latest.json
"""

import json
import os
import sys

HERE = os.path.dirname(__file__)
THRESHOLDS_PATH = os.path.join(HERE, "thresholds.json")
BASELINE_PATH = os.path.join(HERE, "baseline.json")
MAX_DROP = 0.05


def summarize(results: dict, samples: int, commit: str = "", created_at: str = "") -> dict:
    """Turn the per-sample DataFrames from metrics.run_all_metrics into one report."""
    scores = {
        metric: round(float(df[metric].mean()), 3)
        for metric, df in results.items()
        if not df.empty
    }
    return {"created_at": created_at, "commit": commit, "samples": samples, "scores": scores}


def check(report: dict, thresholds: dict, baseline: dict | None = None, max_drop: float = MAX_DROP) -> list:
    """Return a list of human-readable failures. Empty list means the run passes."""
    failures = []
    scores = report["scores"]
    previous = (baseline or {}).get("scores", {})

    for metric, floor in thresholds.items():
        score = scores.get(metric)
        if score is None:
            failures.append(f"{metric}: missing from this run")
            continue
        if score < floor:
            failures.append(f"{metric}: {score:.3f} is below the floor of {floor:.2f}")
        if metric in previous and previous[metric] - score > max_drop:
            failures.append(
                f"{metric}: dropped {previous[metric] - score:.3f} "
                f"(baseline {previous[metric]:.3f} -> {score:.3f})"
            )
    return failures


def print_table(report: dict, thresholds: dict, baseline: dict | None) -> None:
    previous = (baseline or {}).get("scores", {})
    print(f"{'metric':<20}{'score':>8}{'floor':>8}{'baseline':>10}")
    for metric, floor in thresholds.items():
        score = report["scores"].get(metric)
        base = previous.get(metric)
        print(
            f"{metric:<20}"
            f"{'-' if score is None else f'{score:.3f}':>8}"
            f"{floor:>8.2f}"
            f"{'-' if base is None else f'{base:.3f}':>10}"
        )


def load_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def main(report_path: str) -> int:
    report = load_json(report_path)
    thresholds = load_json(THRESHOLDS_PATH)
    baseline = load_json(BASELINE_PATH)

    print_table(report, thresholds, baseline)
    failures = check(report, thresholds, baseline)
    if failures:
        print("\nQuality gate FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("\nQuality gate passed.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python -m evals.gate <report.json>")
    sys.exit(main(sys.argv[1]))
