#!/usr/bin/env python3
"""Run benchmark scenarios against the synthetic OOP fixture project."""

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


def _parse_bool_text(raw: str) -> bool:
    text = str(raw or "").strip().lower()
    return text in {"1", "true", "yes", "on"}


def _normalize_capsule_mode(raw: str) -> str:
    mode = str(raw or "hybrid").strip().lower()
    if mode in {"capsule_only", "capsule", "direct"}:
        return "capsule_only"
    return "hybrid"


def _load_map(path: Path, sep: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or sep not in text:
            continue
        key, raw = text.split(sep, 1)
        key = key.strip()
        value = raw.strip().strip("\"'")
        if key:
            out[key] = value
    return out


def _ensure_openrouter_api_key(framework_root: Path) -> None:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if key:
        return
    env_map = _load_map(framework_root / ".env", "=")
    candidate = str(env_map.get("OPENROUTER_API_KEY", "")).strip()
    if candidate:
        os.environ["OPENROUTER_API_KEY"] = candidate


def _load_config(path: Path) -> dict[str, str]:
    return _load_map(path, ":")


def _write_config(path: Path, values: dict[str, str]) -> None:
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
    capsule_transport_enabled: bool,
    capsule_transport_mode: str,
    capsule_transport_dim: int,
    capsule_transport_max_items: int,
    capsule_transport_fingerprint_bits: int,
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
        "cognition.capsule_transport.enabled": "false",
        "cognition.capsule_transport.mode": "hybrid",
        "cognition.capsule_transport.dim": "768",
        "cognition.capsule_transport.max_items": "48",
        "cognition.capsule_transport.fingerprint_bits": "96",
    }
    framework_cfg = _load_config(framework_root / ".elephant-coder" / "config.md")
    target_cfg_path = target_root / ".elephant-coder" / "config.md"
    target_cfg = _load_config(target_cfg_path)
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
    merged["cognition.capsule_transport.enabled"] = "true" if capsule_transport_enabled else "false"
    merged["cognition.capsule_transport.mode"] = _normalize_capsule_mode(capsule_transport_mode)
    merged["cognition.capsule_transport.dim"] = str(max(128, int(capsule_transport_dim)))
    merged["cognition.capsule_transport.max_items"] = str(
        max(8, int(capsule_transport_max_items))
    )
    merged["cognition.capsule_transport.fingerprint_bits"] = str(
        max(32, int(capsule_transport_fingerprint_bits))
    )
    _write_config(target_cfg_path, merged)


def _count_files(root: Path) -> int:
    skip_parts = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_parts for part in path.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        count += 1
    return count


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
        raise RuntimeError(f"Benchmark runner failed (exit={result.returncode})")
    runs_dir = framework_root / ".elephant-coder" / "runs"
    return json.loads((runs_dir / "benchmark_results.json").read_text(encoding="utf-8"))


def _write_summary(
    *,
    out_path: Path,
    generated_at_utc: str,
    benchmark_id: str,
    target_root: Path,
    fixture_root: Path,
    fixture_file_count: int,
    world_dim: int,
    capsule_dim: int,
    aggregates: dict[str, Any],
) -> None:
    baseline = aggregates.get("baseline", {}) if isinstance(aggregates, dict) else {}
    elephant = aggregates.get("elephant", {}) if isinstance(aggregates, dict) else {}
    lines: list[str] = []
    lines.append("# Dummy OOP Benchmark Summary")
    lines.append("")
    lines.append(f"- generated_at_utc: {generated_at_utc}")
    lines.append(f"- benchmark_id: {benchmark_id}")
    lines.append(f"- target_root: {target_root}")
    lines.append(f"- fixture_root: {fixture_root}")
    lines.append(f"- fixture_file_count: {fixture_file_count}")
    lines.append(f"- world_dim: {world_dim}")
    lines.append(f"- capsule_dim: {capsule_dim}")
    lines.append("")
    lines.append("## Aggregate")
    lines.append(f"- token_reduction_pct: {aggregates.get('token_reduction_pct', 0.0)}")
    lines.append(
        f"- quality_delta_pct_points: {aggregates.get('quality_delta_pct_points', 0.0)}"
    )
    lines.append(f"- latency_delta_ms: {aggregates.get('latency_delta_ms', 0)}")
    lines.append("")
    lines.append("## Modes")
    lines.append(
        f"- baseline: success_rate={baseline.get('success_rate', 0.0)} avg_total_tokens={baseline.get('avg_total_tokens', 0)} total_cost_usd={baseline.get('total_cost_usd', 0.0)}"
    )
    lines.append(
        f"- elephant: success_rate={elephant.get('success_rate', 0.0)} avg_total_tokens={elephant.get('avg_total_tokens', 0)} total_cost_usd={elephant.get('total_cost_usd', 0.0)}"
    )
    lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run dummy OOP benchmark scenario")
    parser.add_argument("--framework-root", default="private/models/elephant-coder")
    parser.add_argument(
        "--fixture-root",
        default=".benchmarks/fixtures/dummy_oop_project",
    )
    parser.add_argument(
        "--tasks-file",
        default=".benchmarks/tasks_dummy_oop_v1.json",
    )
    parser.add_argument("--benchmark-id", default="")
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=0,
        help="Maximum tasks to run (0 means run all tasks).",
    )
    parser.add_argument("--max-input-tokens", type=int, default=24000)
    parser.add_argument("--max-output-tokens", type=int, default=3000)
    parser.add_argument("--max-cost-usd", type=float, default=2.0)
    parser.add_argument("--world-dim", type=int, default=768)
    parser.add_argument("--capsule-dim", type=int, default=48)
    parser.add_argument(
        "--capsule-transport-enabled",
        choices=["true", "false"],
        default="false",
        help="Force capsule transport on/off for benchmark run.",
    )
    parser.add_argument(
        "--capsule-transport-mode",
        choices=["hybrid", "capsule_only"],
        default="hybrid",
    )
    parser.add_argument("--capsule-transport-dim", type=int, default=768)
    parser.add_argument("--capsule-transport-max-items", type=int, default=48)
    parser.add_argument("--capsule-transport-fingerprint-bits", type=int, default=96)
    parser.add_argument(
        "--results-prefix",
        default="dummy_oop",
        help="Artifact prefix under .elephant-coder/runs (default: dummy_oop).",
    )
    args = parser.parse_args()

    framework_root = Path(args.framework_root).resolve()
    fixture_root = Path(args.fixture_root)
    if not fixture_root.is_absolute():
        fixture_root = (framework_root / fixture_root).resolve()
    tasks_path = Path(args.tasks_file)
    if not tasks_path.is_absolute():
        tasks_path = (framework_root / tasks_path).resolve()

    if not fixture_root.exists():
        raise FileNotFoundError(f"Fixture root not found: {fixture_root}")
    fixture_file_count = _count_files(fixture_root)
    if fixture_file_count < 20:
        raise ValueError(
            f"Fixture must contain at least 20 files, found={fixture_file_count}"
        )

    stamp = _sanitize_id(_utc_stamp())
    results_prefix = _sanitize_id(args.results_prefix)
    benchmark_id = (
        _sanitize_id(args.benchmark_id)
        if str(args.benchmark_id).strip()
        else f"{results_prefix}_{stamp}"
    )
    scenario_root = framework_root / ".elephant-coder" / "realworld"
    scenario_root.mkdir(parents=True, exist_ok=True)
    target_root = scenario_root / f"{results_prefix}_{stamp}"
    shutil.copytree(fixture_root, target_root)

    _prepare_target_config(
        framework_root,
        target_root,
        world_dim=int(args.world_dim),
        capsule_dim=int(args.capsule_dim),
        semantic_dims=28,
        capsule_transport_enabled=_parse_bool_text(args.capsule_transport_enabled),
        capsule_transport_mode=str(args.capsule_transport_mode),
        capsule_transport_dim=int(args.capsule_transport_dim),
        capsule_transport_max_items=int(args.capsule_transport_max_items),
        capsule_transport_fingerprint_bits=int(args.capsule_transport_fingerprint_bits),
    )
    _ensure_openrouter_api_key(framework_root)

    payload = _run_benchmark(
        framework_root=framework_root,
        target_root=target_root,
        tasks_file=tasks_path,
        benchmark_id=benchmark_id,
        max_tasks=(None if int(args.max_tasks) <= 0 else int(args.max_tasks)),
        max_input_tokens=int(args.max_input_tokens),
        max_output_tokens=int(args.max_output_tokens),
        max_cost_usd=float(args.max_cost_usd),
    )

    runs_dir = framework_root / ".elephant-coder" / "runs"
    (runs_dir / f"benchmark_results_{results_prefix}.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    shutil.copy2(
        runs_dir / "benchmark_report.md",
        runs_dir / f"benchmark_report_{results_prefix}.md",
    )
    _write_summary(
        out_path=runs_dir / f"{results_prefix}_summary.md",
        generated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        benchmark_id=benchmark_id,
        target_root=target_root,
        fixture_root=fixture_root,
        fixture_file_count=fixture_file_count,
        world_dim=int(args.world_dim),
        capsule_dim=int(args.capsule_dim),
        aggregates=payload.get("aggregates", {}),
    )

    print(
        json.dumps(
            {
                "benchmark_id": benchmark_id,
                "target_root": str(target_root),
                "fixture_file_count": fixture_file_count,
                "aggregates": payload.get("aggregates", {}),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
