#!/usr/bin/env python3
"""Run synthetic benchmark scenarios across multiple fixture projects."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_one(
    *,
    framework_root: Path,
    fixture_root: str,
    tasks_file: str,
    benchmark_id: str,
    results_prefix: str,
    world_dim: int,
    capsule_dim: int,
    max_input_tokens: int,
    max_output_tokens: int,
    max_cost_usd: float,
    max_tasks: int,
    capsule_transport_enabled: str,
    capsule_transport_mode: str,
    capsule_transport_dim: int,
    capsule_transport_max_items: int,
    capsule_transport_fingerprint_bits: int,
) -> dict[str, Any]:
    cmd = [
        "uv",
        "run",
        "--python",
        "3.12",
        "python",
        str(framework_root / "scripts" / "dummy_oop_benchmark_runner.py"),
        "--framework-root",
        str(framework_root),
        "--fixture-root",
        fixture_root,
        "--tasks-file",
        tasks_file,
        "--benchmark-id",
        benchmark_id,
        "--results-prefix",
        results_prefix,
        "--world-dim",
        str(int(world_dim)),
        "--capsule-dim",
        str(int(capsule_dim)),
        "--max-input-tokens",
        str(int(max_input_tokens)),
        "--max-output-tokens",
        str(int(max_output_tokens)),
        "--max-cost-usd",
        str(float(max_cost_usd)),
        "--max-tasks",
        str(int(max_tasks)),
        "--capsule-transport-enabled",
        str(capsule_transport_enabled),
        "--capsule-transport-mode",
        str(capsule_transport_mode),
        "--capsule-transport-dim",
        str(int(capsule_transport_dim)),
        "--capsule-transport-max-items",
        str(int(capsule_transport_max_items)),
        "--capsule-transport-fingerprint-bits",
        str(int(capsule_transport_fingerprint_bits)),
    ]
    result = subprocess.run(
        cmd,
        cwd=str(framework_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.rstrip())
        raise RuntimeError(f"Scenario failed: {results_prefix} (exit={result.returncode})")
    runs_dir = framework_root / ".elephant-coder" / "runs"
    payload_path = runs_dir / f"benchmark_results_{results_prefix}.json"
    return json.loads(payload_path.read_text(encoding="utf-8"))


def _write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    lines.append("# Synthetic Fixture Benchmark Summary")
    lines.append("")
    lines.append(f"- generated_at_utc: {_utc_now()}")
    lines.append("")
    lines.append(
        "| fixture | benchmark_id | world_dim | capsule_dim | baseline_success | elephant_success | token_reduction_pct | quality_delta_pct_points |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['fixture']} | {row['benchmark_id']} | {row['world_dim']} | {row['capsule_dim']} | "
            f"{row['baseline_success_rate']:.2f} | {row['elephant_success_rate']:.2f} | "
            f"{row['token_reduction_pct']:.2f} | {row['quality_delta_pct_points']:.2f} |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run benchmarks across all synthetic fixtures")
    parser.add_argument("--framework-root", default="private/models/elephant-coder")
    parser.add_argument("--max-input-tokens", type=int, default=24000)
    parser.add_argument("--max-output-tokens", type=int, default=3000)
    parser.add_argument("--max-cost-usd", type=float, default=2.0)
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=0,
        help="Maximum tasks per fixture (0 means all).",
    )
    parser.add_argument(
        "--capsule-transport-enabled",
        choices=["true", "false"],
        default="false",
    )
    parser.add_argument(
        "--capsule-transport-mode",
        choices=["hybrid", "capsule_only"],
        default="hybrid",
    )
    parser.add_argument("--capsule-transport-dim", type=int, default=768)
    parser.add_argument("--capsule-transport-max-items", type=int, default=48)
    parser.add_argument("--capsule-transport-fingerprint-bits", type=int, default=96)
    args = parser.parse_args()

    framework_root = Path(args.framework_root).resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    scenarios = [
        {
            "fixture": "dummy_oop",
            "fixture_root": ".benchmarks/fixtures/dummy_oop_project",
            "tasks_file": ".benchmarks/tasks_dummy_oop_v1.json",
            "results_prefix": "dummy_oop",
            "world_dim": 768,
            "capsule_dim": 48,
        },
        {
            "fixture": "dummy_event_mesh",
            "fixture_root": ".benchmarks/fixtures/dummy_event_mesh_project",
            "tasks_file": ".benchmarks/tasks_dummy_event_mesh_v1.json",
            "results_prefix": "dummy_event_mesh",
            "world_dim": 896,
            "capsule_dim": 56,
        },
        {
            "fixture": "dummy_policy_engine",
            "fixture_root": ".benchmarks/fixtures/dummy_policy_engine_project",
            "tasks_file": ".benchmarks/tasks_dummy_policy_engine_v1.json",
            "results_prefix": "dummy_policy_engine",
            "world_dim": 1024,
            "capsule_dim": 64,
        },
        {
            "fixture": "dummy_layered_inheritance",
            "fixture_root": ".benchmarks/fixtures/dummy_layered_inheritance_project",
            "tasks_file": ".benchmarks/tasks_dummy_layered_inheritance_v1.json",
            "results_prefix": "dummy_layered_inheritance",
            "world_dim": 1152,
            "capsule_dim": 72,
        },
        {
            "fixture": "dummy_cross_module",
            "fixture_root": ".benchmarks/fixtures/dummy_cross_module_project",
            "tasks_file": ".benchmarks/tasks_dummy_cross_module_v1.json",
            "results_prefix": "dummy_cross_module",
            "world_dim": 1280,
            "capsule_dim": 80,
        },
    ]

    summary_rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        benchmark_id = f"{scenario['results_prefix']}_{stamp}"
        payload = _run_one(
            framework_root=framework_root,
            fixture_root=scenario["fixture_root"],
            tasks_file=scenario["tasks_file"],
            benchmark_id=benchmark_id,
            results_prefix=scenario["results_prefix"],
            world_dim=int(scenario["world_dim"]),
            capsule_dim=int(scenario["capsule_dim"]),
            max_input_tokens=int(args.max_input_tokens),
            max_output_tokens=int(args.max_output_tokens),
            max_cost_usd=float(args.max_cost_usd),
            max_tasks=int(args.max_tasks),
            capsule_transport_enabled=str(args.capsule_transport_enabled),
            capsule_transport_mode=str(args.capsule_transport_mode),
            capsule_transport_dim=int(args.capsule_transport_dim),
            capsule_transport_max_items=int(args.capsule_transport_max_items),
            capsule_transport_fingerprint_bits=int(args.capsule_transport_fingerprint_bits),
        )
        aggregates = payload.get("aggregates", {})
        baseline = aggregates.get("baseline", {})
        elephant = aggregates.get("elephant", {})
        summary_rows.append(
            {
                "fixture": scenario["fixture"],
                "benchmark_id": benchmark_id,
                "world_dim": int(scenario["world_dim"]),
                "capsule_dim": int(scenario["capsule_dim"]),
                "baseline_success_rate": float(baseline.get("success_rate", 0.0) or 0.0),
                "elephant_success_rate": float(elephant.get("success_rate", 0.0) or 0.0),
                "token_reduction_pct": float(aggregates.get("token_reduction_pct", 0.0) or 0.0),
                "quality_delta_pct_points": float(
                    aggregates.get("quality_delta_pct_points", 0.0) or 0.0
                ),
            }
        )

    summary_path = framework_root / ".elephant-coder" / "runs" / "multi_fixture_summary.md"
    _write_summary(summary_path, summary_rows)
    print(json.dumps({"summary_path": str(summary_path), "rows": summary_rows}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
