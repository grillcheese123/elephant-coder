#!/usr/bin/env python3
"""Run real-world quality benchmarks on existing and scratch repositories."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sanitize_id(raw: str) -> str:
    value = "".join(ch for ch in str(raw).strip() if ch.isalnum() or ch in {"-", "_"})
    return value or "run"


def _load_config_map(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or ":" not in text:
            continue
        key, raw = text.split(":", 1)
        key = key.strip()
        value = raw.strip()
        if key:
            out[key] = value
    return out


def _load_dotenv_map(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, raw = text.split("=", 1)
        key = key.strip()
        value = raw.strip().strip("\"'")
        if key:
            out[key] = value
    return out


def _ensure_openrouter_api_key(framework_root: Path) -> None:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if key:
        return
    env_map = _load_dotenv_map(framework_root / ".env")
    candidate = str(env_map.get("OPENROUTER_API_KEY", "")).strip()
    if candidate:
        os.environ["OPENROUTER_API_KEY"] = candidate


def _write_config_map(path: Path, values: dict[str, str]) -> None:
    lines = ["# Elephant Coder Config", ""]
    for key in sorted(values):
        lines.append(f"{key}: {values[key]}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _prepare_target_config(
    framework_root: Path,
    target_root: Path,
    *,
    world_dim: int,
    capsule_dim: int,
    semantic_dims: int,
) -> None:
    defaults = {
        "output.default": "text",
        "model.default": "gpt-4o-mini",
        "model.fallbacks": "",
        "model.max_retries": "2",
        "model.retry_backoff_sec": "1.0",
        "budgets.max_input_tokens": "12000",
        "budgets.max_output_tokens": "3000",
        "budgets.max_cost_usd": "1.0",
        "plugins.allowed_permissions": "read_fs",
        "cognition.world_model.enabled": "true",
        "cognition.world_model.max_edge_facts": "20000",
        "cognition.world_model.max_symbol_facts": "5000",
    }
    framework_cfg = _load_config_map(framework_root / ".elephant-coder" / "config.md")
    target_cfg_path = target_root / ".elephant-coder" / "config.md"
    target_cfg = _load_config_map(target_cfg_path)
    merged = dict(defaults)
    merged.update(framework_cfg)
    merged.update(target_cfg)
    merged["cognition.world_model.enabled"] = "true"
    merged["cognition.world_model.dim"] = str(max(64, int(world_dim)))
    merged["cognition.world_model.capsule_dim"] = str(max(0, int(capsule_dim)))
    semantic = max(1, int(semantic_dims))
    if int(merged["cognition.world_model.capsule_dim"]) > 0 and semantic >= int(
        merged["cognition.world_model.capsule_dim"]
    ):
        semantic = max(1, int(merged["cognition.world_model.capsule_dim"]) - 4)
    merged["cognition.world_model.semantic_dims"] = str(semantic)
    _write_config_map(target_cfg_path, merged)


def _copy_existing_repo(source_root: Path, target_root: Path) -> None:
    ignore = shutil.ignore_patterns(
        ".git",
        ".elephant-coder",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "node_modules",
        "dist",
        "build",
        ".venv",
        "venv",
    )
    shutil.copytree(source_root, target_root, ignore=ignore)


def _run_benchmark(
    *,
    framework_root: Path,
    target_root: Path,
    tasks_file: Path,
    benchmark_id: str,
    max_tasks: int | None,
    max_input_tokens: int,
    max_output_tokens: int,
    max_cost_usd: float,
) -> dict[str, Any]:
    cmd = [
        "uv",
        "run",
        "--python",
        "3.12",
        "python",
        str(framework_root / "scripts" / "benchmark_runner.py"),
        "--cwd",
        str(framework_root),
        "--target-cwd",
        str(target_root),
        "--tasks-file",
        str(tasks_file),
        "--comparison-track",
        "strategy",
        "--benchmark-id",
        benchmark_id,
        "--max-input-tokens",
        str(int(max_input_tokens)),
        "--max-output-tokens",
        str(int(max_output_tokens)),
        "--max-cost-usd",
        str(float(max_cost_usd)),
        "--apply",
        "--run-checks",
    ]
    if max_tasks is not None and int(max_tasks) > 0:
        cmd.extend(["--max-tasks", str(int(max_tasks))])
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
        raise RuntimeError(f"Benchmark runner failed for {benchmark_id} (exit={result.returncode})")
    runs_dir = framework_root / ".elephant-coder" / "runs"
    payload = json.loads((runs_dir / "benchmark_results.json").read_text(encoding="utf-8"))
    return payload


def _extract_summary(payload: dict[str, Any]) -> dict[str, Any]:
    aggregates = payload.get("aggregates", {})
    baseline = aggregates.get("baseline", {}) if isinstance(aggregates, dict) else {}
    elephant = aggregates.get("elephant", {}) if isinstance(aggregates, dict) else {}
    return {
        "benchmark_id": str(payload.get("benchmark_id", "")),
        "tasks_total": int(payload.get("tasks_total", 0) or 0),
        "runs_total": int(payload.get("runs_total", 0) or 0),
        "token_reduction_pct": float(aggregates.get("token_reduction_pct", 0.0) or 0.0),
        "quality_delta_pct_points": float(aggregates.get("quality_delta_pct_points", 0.0) or 0.0),
        "latency_delta_ms": int(aggregates.get("latency_delta_ms", 0) or 0),
        "baseline_success_rate": float(baseline.get("success_rate", 0.0) or 0.0),
        "elephant_success_rate": float(elephant.get("success_rate", 0.0) or 0.0),
        "baseline_avg_total_tokens": int(baseline.get("avg_total_tokens", 0) or 0),
        "elephant_avg_total_tokens": int(elephant.get("avg_total_tokens", 0) or 0),
        "baseline_total_cost_usd": float(baseline.get("total_cost_usd", 0.0) or 0.0),
        "elephant_total_cost_usd": float(elephant.get("total_cost_usd", 0.0) or 0.0),
    }


def _write_report(
    *,
    out_path: Path,
    generated_at_utc: str,
    existing_summary: dict[str, Any],
    scratch_summary: dict[str, Any],
    existing_dim: int,
    existing_capsule_dim: int,
    scratch_dim: int,
    scratch_capsule_dim: int,
    existing_target: Path,
    scratch_target: Path,
) -> None:
    lines: list[str] = []
    lines.append("# Real-World Quality Report")
    lines.append("")
    lines.append(f"- generated_at_utc: {generated_at_utc}")
    lines.append(f"- existing_target_root: {existing_target}")
    lines.append(f"- scratch_target_root: {scratch_target}")
    lines.append(
        f"- existing_dimensions: world_dim={existing_dim}, capsule_dim={existing_capsule_dim}"
    )
    lines.append(
        f"- scratch_dimensions: world_dim={scratch_dim}, capsule_dim={scratch_capsule_dim}"
    )
    lines.append("")
    lines.append("## Scenario Comparison")
    lines.append("| metric | existing_repo | scratch_repo |")
    lines.append("|---|---:|---:|")
    lines.append(
        f"| benchmark_id | {existing_summary['benchmark_id']} | {scratch_summary['benchmark_id']} |"
    )
    lines.append(
        f"| tasks_total | {existing_summary['tasks_total']} | {scratch_summary['tasks_total']} |"
    )
    lines.append(
        f"| token_reduction_pct | {existing_summary['token_reduction_pct']:.2f} | {scratch_summary['token_reduction_pct']:.2f} |"
    )
    lines.append(
        f"| quality_delta_pct_points | {existing_summary['quality_delta_pct_points']:.2f} | {scratch_summary['quality_delta_pct_points']:.2f} |"
    )
    lines.append(
        f"| baseline_success_rate | {existing_summary['baseline_success_rate']:.2f} | {scratch_summary['baseline_success_rate']:.2f} |"
    )
    lines.append(
        f"| elephant_success_rate | {existing_summary['elephant_success_rate']:.2f} | {scratch_summary['elephant_success_rate']:.2f} |"
    )
    lines.append(
        f"| baseline_avg_total_tokens | {existing_summary['baseline_avg_total_tokens']} | {scratch_summary['baseline_avg_total_tokens']} |"
    )
    lines.append(
        f"| elephant_avg_total_tokens | {existing_summary['elephant_avg_total_tokens']} | {scratch_summary['elephant_avg_total_tokens']} |"
    )
    lines.append(
        f"| baseline_total_cost_usd | {existing_summary['baseline_total_cost_usd']:.6f} | {scratch_summary['baseline_total_cost_usd']:.6f} |"
    )
    lines.append(
        f"| elephant_total_cost_usd | {existing_summary['elephant_total_cost_usd']:.6f} | {scratch_summary['elephant_total_cost_usd']:.6f} |"
    )
    lines.append(
        f"| latency_delta_ms | {existing_summary['latency_delta_ms']} | {scratch_summary['latency_delta_ms']} |"
    )
    lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real-world quality scenarios")
    parser.add_argument("--framework-root", default="private/models/elephant-coder")
    parser.add_argument("--existing-source-root", default="")
    parser.add_argument(
        "--existing-tasks-file",
        default=".benchmarks/tasks_realworld_existing_v1.json",
    )
    parser.add_argument(
        "--scratch-tasks-file",
        default=".benchmarks/tasks_realworld_scratch_v1.json",
    )
    parser.add_argument("--existing-max-tasks", type=int, default=3)
    parser.add_argument("--scratch-max-tasks", type=int, default=3)
    parser.add_argument("--max-input-tokens", type=int, default=24000)
    parser.add_argument("--max-output-tokens", type=int, default=3000)
    parser.add_argument("--max-cost-usd", type=float, default=2.0)
    parser.add_argument("--existing-world-dim", type=int, default=512)
    parser.add_argument("--existing-capsule-dim", type=int, default=32)
    parser.add_argument("--scratch-world-dim", type=int, default=1024)
    parser.add_argument("--scratch-capsule-dim", type=int, default=64)
    args = parser.parse_args()

    framework_root = Path(args.framework_root).resolve()
    existing_source_root = (
        Path(args.existing_source_root).resolve()
        if str(args.existing_source_root).strip()
        else framework_root
    )
    existing_tasks = Path(args.existing_tasks_file)
    if not existing_tasks.is_absolute():
        existing_tasks = (framework_root / existing_tasks).resolve()
    scratch_tasks = Path(args.scratch_tasks_file)
    if not scratch_tasks.is_absolute():
        scratch_tasks = (framework_root / scratch_tasks).resolve()

    stamp = _sanitize_id(_utc_stamp())
    scenario_root = framework_root / ".elephant-coder" / "realworld"
    scenario_root.mkdir(parents=True, exist_ok=True)
    existing_target = scenario_root / f"existing_repo_{stamp}"
    scratch_target = scenario_root / f"scratch_repo_{stamp}"

    _copy_existing_repo(existing_source_root, existing_target)
    scratch_target.mkdir(parents=True, exist_ok=True)
    (scratch_target / ".gitignore").write_text("__pycache__/\n.venv/\n", encoding="utf-8")

    _prepare_target_config(
        framework_root,
        existing_target,
        world_dim=int(args.existing_world_dim),
        capsule_dim=int(args.existing_capsule_dim),
        semantic_dims=28,
    )
    _prepare_target_config(
        framework_root,
        scratch_target,
        world_dim=int(args.scratch_world_dim),
        capsule_dim=int(args.scratch_capsule_dim),
        semantic_dims=28,
    )
    _ensure_openrouter_api_key(framework_root)

    existing_benchmark_id = f"realworld_existing_{stamp}"
    scratch_benchmark_id = f"realworld_scratch_{stamp}"

    existing_payload = _run_benchmark(
        framework_root=framework_root,
        target_root=existing_target,
        tasks_file=existing_tasks,
        benchmark_id=existing_benchmark_id,
        max_tasks=int(args.existing_max_tasks),
        max_input_tokens=int(args.max_input_tokens),
        max_output_tokens=int(args.max_output_tokens),
        max_cost_usd=float(args.max_cost_usd),
    )
    runs_dir = framework_root / ".elephant-coder" / "runs"
    (runs_dir / "benchmark_results_realworld_existing.json").write_text(
        json.dumps(existing_payload, indent=2), encoding="utf-8"
    )
    shutil.copy2(
        runs_dir / "benchmark_report.md",
        runs_dir / "benchmark_report_realworld_existing.md",
    )

    scratch_payload = _run_benchmark(
        framework_root=framework_root,
        target_root=scratch_target,
        tasks_file=scratch_tasks,
        benchmark_id=scratch_benchmark_id,
        max_tasks=int(args.scratch_max_tasks),
        max_input_tokens=int(args.max_input_tokens),
        max_output_tokens=int(args.max_output_tokens),
        max_cost_usd=float(args.max_cost_usd),
    )
    (runs_dir / "benchmark_results_realworld_scratch.json").write_text(
        json.dumps(scratch_payload, indent=2), encoding="utf-8"
    )
    shutil.copy2(
        runs_dir / "benchmark_report.md",
        runs_dir / "benchmark_report_realworld_scratch.md",
    )

    existing_summary = _extract_summary(existing_payload)
    scratch_summary = _extract_summary(scratch_payload)
    report_path = runs_dir / "realworld_quality_report.md"
    _write_report(
        out_path=report_path,
        generated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        existing_summary=existing_summary,
        scratch_summary=scratch_summary,
        existing_dim=int(args.existing_world_dim),
        existing_capsule_dim=int(args.existing_capsule_dim),
        scratch_dim=int(args.scratch_world_dim),
        scratch_capsule_dim=int(args.scratch_capsule_dim),
        existing_target=existing_target,
        scratch_target=scratch_target,
    )

    print(f"Existing summary: {json.dumps(existing_summary)}")
    print(f"Scratch summary: {json.dumps(scratch_summary)}")
    print(f"Report written: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
