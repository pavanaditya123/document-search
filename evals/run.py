"""
Run the whole eval suite from the command line and gate on the result.

Needs the API running (uvicorn app.main:app --port 8000) and the keys in .env.

    python -m evals.run                     # run, save report, apply the gate
    python -m evals.run --update-baseline   # also accept this run as the new baseline

Reports go to evals/reports/<timestamp>.json, plus a copy at latest.json.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from evals import gate
from evals.metrics import run_all_metrics
from evals.pipeline import load_golden_dataset, run_pipeline

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def current_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main(update_baseline: bool) -> int:
    golden = load_golden_dataset()
    print(f"Phase 1: querying the live API with {len(golden['rag_samples'])} golden questions...")
    answered = run_pipeline(golden)

    print("Phase 2: scoring with RAGAS (slow on purpose, to stay inside Groq rate limits)...")
    results = asyncio.run(run_all_metrics(answered, status_cb=print))

    now = datetime.now(timezone.utc)
    report = gate.summarize(
        results,
        samples=len(answered["rag_samples"]),
        commit=current_commit(),
        created_at=now.isoformat(timespec="seconds"),
    )

    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"{now:%Y%m%d-%H%M%S}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    shutil.copy(report_path, os.path.join(REPORTS_DIR, "latest.json"))
    print(f"Saved {report_path}\n")

    status = gate.main(report_path)
    if update_baseline:
        if status != 0:
            print("Not updating the baseline: this run failed the gate.")
        else:
            shutil.copy(report_path, gate.BASELINE_PATH)
            print(f"Baseline updated to {report_path}")
    return status


if __name__ == "__main__":
    sys.exit(main(update_baseline="--update-baseline" in sys.argv))
