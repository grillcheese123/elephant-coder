#!/usr/bin/env python3
"""Benchmark runner for Elephant Coder protocol v1."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_benchmark_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"bench_{stamp}_{os.getpid()}"


def _sanitize_id(raw: str) -> str:
    value = "".join(ch for ch in str(raw).strip() if ch.isalnum() or ch in {"-", "_"})
    if not value:
        raise ValueError("benchmark/session id must contain at least one valid character")
    return value


def _session_log_path(project_root: Path, session_id: str) -> Path:
    safe = _sanitize_id(session_id)
    return project_root / ".elephant-coder" / "sessions" / f"{safe}.jsonl"


def _load_cli_module(project_root: Path):
    cli_path = project_root / "scripts" / "elephant_cli.py"
    spec = importlib.util.spec_from_file_location("elephant_cli_benchmark", cli_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load CLI from {cli_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class BenchmarkTask:
    task_id: str
    category: str
    prompt: str
    checks: list[str]
    expected_files: list[str]


def _load_tasks(tasks_path: Path) -> list[BenchmarkTask]:
    if not tasks_path.exists():
        raise FileNotFoundError(
            f"Task file not found: {tasks_path}. "
            "Create it from .benchmarks/tasks_v1.json template."
        )
    payload = json.loads(tasks_path.read_text(encoding="utf-8", errors="replace"))
    raw_tasks = payload.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raise ValueError("tasks must be a list")
    out: list[BenchmarkTask] = []
    for item in raw_tasks:
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("task_id", "")).strip()
        prompt = str(item.get("prompt", "")).strip()
        if not task_id or not prompt:
            continue
        category = str(item.get("category", "unspecified")).strip() or "unspecified"
        checks_raw = item.get("checks", [])
        checks = [str(cmd).strip() for cmd in checks_raw if str(cmd).strip()] if isinstance(checks_raw, list) else []
        exp_raw = item.get("expected_files", [])
        expected_files = [str(path).strip() for path in exp_raw if str(path).strip()] if isinstance(exp_raw, list) else []
        out.append(
            BenchmarkTask(
                task_id=task_id,
                category=category,
                prompt=prompt,
                checks=checks,
                expected_files=expected_files,
            )
        )
    if not out:
        raise ValueError(f"No valid tasks in {tasks_path}")
    return out


def _run_checks(project_root: Path, checks: list[str]) -> tuple[list[str], list[str]]:
    passed: list[str] = []
    failed: list[str] = []
    for cmd in checks:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(project_root),
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            passed.append(cmd)
        else:
            err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
            failed.append(f"{cmd} (code={result.returncode}{'; ' + err if err else ''})")
    return passed, failed


def _summarize_mode(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "runs": 0,
            "success_rate": 0.0,
            "avg_total_tokens": 0,
            "avg_latency_ms": 0,
            "total_cost_usd": 0.0,
        }
    success = sum(1 for row in rows if bool(row.get("success", False)))
    total_tokens = [int(row.get("total_tokens", 0) or 0) for row in rows]
    latency = [int(row.get("latency_ms", 0) or 0) for row in rows]
    total_cost = sum(float(row.get("estimated_cost_usd", 0.0) or 0.0) for row in rows)
    return {
        "runs": len(rows),
        "success_rate": round((success / len(rows)) * 100.0, 2),
        "avg_total_tokens": int(mean(total_tokens)) if total_tokens else 0,
        "avg_latency_ms": int(mean(latency)) if latency else 0,
        "total_cost_usd": round(total_cost, 6),
    }


def _build_report_md(results: dict[str, Any]) -> str:
    aggregates = results.get("aggregates", {})
    baseline = aggregates.get("baseline", {})
    elephant = aggregates.get("elephant", {})
    rows = results.get("results", [])
    lines: list[str] = []
    lines.append("# Elephant Benchmark Report")
    lines.append("")
    lines.append(f"- generated_at_utc: {results.get('generated_at_utc', '')}")
    lines.append(f"- benchmark_id: {results.get('benchmark_id', '')}")
    lines.append(f"- protocol_version: {results.get('protocol_version', 'v1')}")
    lines.append(f"- comparison_track: {results.get('comparison_track', 'strategy')}")
    lines.append(f"- tasks_total: {results.get('tasks_total', 0)}")
    lines.append(f"- runs_total: {results.get('runs_total', 0)}")
    lines.append("")
    lines.append("## Aggregate")
    lines.append(f"- token_reduction_pct: {aggregates.get('token_reduction_pct', 0.0)}")
    lines.append(f"- quality_delta_pct_points: {aggregates.get('quality_delta_pct_points', 0.0)}")
    lines.append(f"- latency_delta_ms: {aggregates.get('latency_delta_ms', 0)}")
    lines.append("")
    lines.append("## Mode Summary")
    lines.append(
        "| mode | runs | success_rate | avg_total_tokens | avg_latency_ms | total_cost_usd |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|")
    lines.append(
        f"| baseline | {baseline.get('runs', 0)} | {baseline.get('success_rate', 0.0)} | "
        f"{baseline.get('avg_total_tokens', 0)} | {baseline.get('avg_latency_ms', 0)} | "
        f"{baseline.get('total_cost_usd', 0.0)} |"
    )
    lines.append(
        f"| elephant | {elephant.get('runs', 0)} | {elephant.get('success_rate', 0.0)} | "
        f"{elephant.get('avg_total_tokens', 0)} | {elephant.get('avg_latency_ms', 0)} | "
        f"{elephant.get('total_cost_usd', 0.0)} |"
    )
    lines.append("")
    lines.append("## Per-Task Runs")
    lines.append(
        "| task_id | mode | success | total_tokens | latency_ms | cost_usd | retries | selected_model |"
    )
    lines.append("|---|---|---|---:|---:|---:|---:|---|")
    for row in rows:
        lines.append(
            f"| {row.get('task_id', '')} | {row.get('mode', '')} | {bool(row.get('success', False))} | "
            f"{int(row.get('total_tokens', 0) or 0)} | {int(row.get('latency_ms', 0) or 0)} | "
            f"{float(row.get('estimated_cost_usd', 0.0) or 0.0):.6f} | {int(row.get('retries', 0) or 0)} | "
            f"{row.get('selected_model', '')} |"
        )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Elephant benchmark protocol v1")
    parser.add_argument(
        "--cwd",
        default=".",
        help="Elephant framework root (default: current directory)",
    )
    parser.add_argument(
        "--target-cwd",
        default="",
        help=(
            "Target repository root for command execution. "
            "Defaults to --cwd when omitted."
        ),
    )
    parser.add_argument(
        "--tasks-file",
        default=".benchmarks/tasks_v1.json",
        help="Task suite JSON path (project-relative or absolute)",
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--max-tasks", type=int, default=None)
    parser.add_argument("--max-input-tokens", type=int, default=24000)
    parser.add_argument("--max-output-tokens", type=int, default=3000)
    parser.add_argument("--max-cost-usd", type=float, default=2.0)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Skip model execution and run /code in dry-run mode (tokens/cost will be zero).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Allow apply-to-disk (default is inference-only with --no-apply).",
    )
    parser.add_argument(
        "--run-checks",
        action="store_true",
        default=False,
        help="Execute per-task checks after each run (requires --apply).",
    )
    parser.add_argument(
        "--benchmark-id",
        default="",
        help=(
            "Benchmark run identifier used to namespace benchmark sessions. "
            "Default is generated per invocation."
        ),
    )
    parser.add_argument(
        "--comparison-track",
        choices=["strategy", "prompt-parity"],
        default="strategy",
        help=(
            "Benchmark comparison strategy: "
            "'strategy' keeps mode-specific behavior, "
            "'prompt-parity' forces identical prompt-construction behavior."
        ),
    )
    args = parser.parse_args()

    framework_root = Path(args.cwd).resolve()
    target_root = Path(args.target_cwd).resolve() if str(args.target_cwd).strip() else framework_root
    if not target_root.exists():
        raise FileNotFoundError(f"Target repository root does not exist: {target_root}")
    tasks_path = Path(args.tasks_file)
    if not tasks_path.is_absolute():
        tasks_path = (framework_root / tasks_path).resolve()
    tasks = _load_tasks(tasks_path)
    if args.max_tasks is not None and args.max_tasks > 0:
        tasks = tasks[: args.max_tasks]

    repeats = max(1, int(args.repeats))
    dry_run = bool(args.dry_run)
    apply_to_disk = bool(args.apply)
    if dry_run and apply_to_disk:
        raise ValueError("Use either --dry-run or --apply, not both.")
    no_apply = not dry_run and not apply_to_disk
    run_checks = bool(args.run_checks) and apply_to_disk and not dry_run
    benchmark_id = _sanitize_id(args.benchmark_id) if str(args.benchmark_id).strip() else _default_benchmark_id()
    comparison_track = str(args.comparison_track or "strategy").strip().lower()
    if comparison_track not in {"strategy", "prompt-parity"}:
        raise ValueError(f"Unsupported comparison track: {comparison_track}")
    benchmark_parity = comparison_track == "prompt-parity"

    cli = _load_cli_module(framework_root)
    mode_order = ("baseline", "elephant")
    parser_cli = cli._build_parser()

    all_rows: list[dict[str, Any]] = []
    print(f"Benchmark start: tasks={len(tasks)} repeats={repeats} dry_run={dry_run} "
          f"apply={apply_to_disk} no_apply={no_apply} modes={','.join(mode_order)} "
          f"benchmark_id={benchmark_id} comparison_track={comparison_track} "
          f"framework_root={framework_root} target_root={target_root}")

    previous_project_root_env = os.getenv("ELEPHANT_PROJECT_ROOT")
    os.environ["ELEPHANT_PROJECT_ROOT"] = str(target_root)
    try:
        for rep in range(1, repeats + 1):
            for task in tasks:
                for mode in mode_order:
                    session_id = f"{benchmark_id}_{task.task_id}_{mode}_r{rep}"
                    # Avoid leakage from previous benchmark invocations.
                    _session_log_path(target_root, session_id).unlink(missing_ok=True)
                    argv = [
                        "code",
                        "--cwd",
                        str(target_root),
                        "--task",
                        task.prompt,
                        "--mode",
                        mode,
                        "--output",
                        "json",
                        "--session",
                        session_id,
                        "--max-input-tokens",
                        str(int(args.max_input_tokens)),
                        "--max-output-tokens",
                        str(int(args.max_output_tokens)),
                        "--max-cost-usd",
                        str(float(args.max_cost_usd)),
                    ]
                    if dry_run:
                        argv.append("--dry-run")
                    if no_apply:
                        argv.append("--no-apply")
                    if benchmark_parity:
                        argv.append("--benchmark-parity")
                    cmd_args = cli._parse(parser_cli, argv)
                    exit_code, response = cli.execute_command(cmd_args)
                    ok = bool(response.get("ok", False)) and exit_code == 0
                    metrics = response.get("metrics", {}) or {}
                    data = response.get("data", {}) or {}
                    checks_passed: list[str] = []
                    checks_failed: list[str] = []
                    if ok and run_checks and task.checks:
                        checks_passed, checks_failed = _run_checks(target_root, task.checks)
                    success = ok and not checks_failed
                    row = {
                        "task_id": task.task_id,
                        "category": task.category,
                        "prompt": task.prompt,
                        "mode": mode,
                        "repeat": rep,
                        "benchmark_id": benchmark_id,
                        "comparison_track": comparison_track,
                        "session_id": session_id,
                        "run_id": str(response.get("run_id", "")),
                        "success": success,
                        "ok": ok,
                        "input_tokens": int(metrics.get("input_tokens", 0) or 0),
                        "output_tokens": int(metrics.get("output_tokens", 0) or 0),
                        "total_tokens": int(metrics.get("total_tokens", 0) or 0),
                        "estimated_cost_usd": float(metrics.get("estimated_cost_usd", 0.0) or 0.0),
                        "latency_ms": int(metrics.get("latency_ms", 0) or 0),
                        "retries": int(data.get("retry_count", 0) or 0),
                        "selected_model": str(data.get("selected_model", "")),
                        "files_touched": list(data.get("files_touched", []) or []),
                        "checks_passed": checks_passed,
                        "checks_failed": checks_failed,
                        "errors": response.get("errors", []) or [],
                        "warnings": response.get("warnings", []) or [],
                    }
                    all_rows.append(row)
                    print(
                        f"[{mode}] {task.task_id} r{rep} ok={ok} success={success} "
                        f"tokens={row['total_tokens']} latency_ms={row['latency_ms']} retries={row['retries']}"
                    )
    finally:
        if previous_project_root_env is None:
            os.environ.pop("ELEPHANT_PROJECT_ROOT", None)
        else:
            os.environ["ELEPHANT_PROJECT_ROOT"] = previous_project_root_env

    baseline_rows = [row for row in all_rows if row["mode"] == "baseline"]
    elephant_rows = [row for row in all_rows if row["mode"] == "elephant"]
    baseline = _summarize_mode(baseline_rows)
    elephant = _summarize_mode(elephant_rows)
    token_reduction_pct = 0.0
    if int(baseline.get("avg_total_tokens", 0)) > 0:
        token_reduction_pct = round(
            (
                (int(baseline["avg_total_tokens"]) - int(elephant.get("avg_total_tokens", 0)))
                / int(baseline["avg_total_tokens"])
            )
            * 100.0,
            2,
        )
    quality_delta = round(
        float(elephant.get("success_rate", 0.0)) - float(baseline.get("success_rate", 0.0)),
        2,
    )
    latency_delta = int(elephant.get("avg_latency_ms", 0)) - int(baseline.get("avg_latency_ms", 0))

    results = {
        "protocol_version": "v1",
        "generated_at_utc": _utc_now_iso(),
        "benchmark_id": benchmark_id,
        "comparison_track": comparison_track,
        "framework_root": str(framework_root),
        "project_root": str(target_root),
        "tasks_source": str(tasks_path),
        "tasks_total": len(tasks),
        "runs_total": len(all_rows),
        "dry_run": dry_run,
        "apply_to_disk": apply_to_disk,
        "no_apply": no_apply,
        "run_checks": run_checks,
        "budget_overrides": {
            "max_input_tokens": int(args.max_input_tokens),
            "max_output_tokens": int(args.max_output_tokens),
            "max_cost_usd": float(args.max_cost_usd),
        },
        "results": all_rows,
        "aggregates": {
            "baseline": baseline,
            "elephant": elephant,
            "token_reduction_pct": token_reduction_pct,
            "quality_delta_pct_points": quality_delta,
            "latency_delta_ms": latency_delta,
        },
    }

    runs_dir = framework_root / ".elephant-coder" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    results_path = runs_dir / "benchmark_results.json"
    report_path = runs_dir / "benchmark_report.md"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    report_path.write_text(_build_report_md(results), encoding="utf-8")

    print(f"Results written: {results_path}")
    print(f"Report written: {report_path}")
    print(
        "Aggregate: "
        f"token_reduction_pct={results['aggregates']['token_reduction_pct']} "
        f"quality_delta_pct_points={results['aggregates']['quality_delta_pct_points']} "
        f"latency_delta_ms={results['aggregates']['latency_delta_ms']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
