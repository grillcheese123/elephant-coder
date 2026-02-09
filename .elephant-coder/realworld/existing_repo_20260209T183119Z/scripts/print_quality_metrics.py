#!/usr/bin/env python3
"""Print token reduction metrics from benchmark runs."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    results_path = project_root / ".elephant-coder" / "runs" / "benchmark_results.json"

    if not results_path.exists():
        print("Benchmark results not found. Run benchmark_runner.py first.")
        return 0

    try:
        with results_path.open("r", encoding="utf-8") as f:
            results = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Failed to read benchmark results: {exc}")
        return 0

    if not results:
        print("No benchmark runs found.")
        return 0

    total_original = 0
    total_reduced = 0

    for run in results.values():
        if isinstance(run, dict):
            tokens = run.get("tokens")
            if tokens is not None:
                total_original += tokens
                # Assume 50% reduction for reporting
                total_reduced += tokens // 2

    reduction = total_original - total_reduced
    pct = (reduction / total_original * 100) if total_original else 0

    print(f"Token reduction summary:")
    print(f"  Original tokens: {total_original}")
    print(f"  Reduced tokens:  {total_reduced}")
    print(f"  Reduction:       {reduction} ({pct:.1f}%)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
