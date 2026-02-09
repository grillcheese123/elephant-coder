"""Tests for benchmark runner helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_runner_module():
    root = Path(__file__).resolve().parents[1]
    runner_path = root / "scripts" / "benchmark_runner.py"
    spec = importlib.util.spec_from_file_location("benchmark_runner_local", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scripts/benchmark_runner.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


benchmark_runner = _load_runner_module()


def test_default_benchmark_id_has_prefix():
    value = benchmark_runner._default_benchmark_id()
    assert value.startswith("bench_")


def test_sanitize_id_rejects_invalid_text():
    failed = False
    try:
        benchmark_runner._sanitize_id("%%%")
    except ValueError:
        failed = True
    assert failed is True


def test_build_report_includes_comparison_track():
    payload = {
        "generated_at_utc": "2026-02-09T00:00:00Z",
        "benchmark_id": "bench_test",
        "comparison_track": "prompt-parity",
        "protocol_version": "v1",
        "tasks_total": 1,
        "runs_total": 2,
        "results": [],
        "aggregates": {
            "token_reduction_pct": 0.0,
            "quality_delta_pct_points": 0.0,
            "latency_delta_ms": 0,
            "baseline": {
                "runs": 1,
                "success_rate": 100.0,
                "avg_total_tokens": 10,
                "avg_latency_ms": 10,
                "total_cost_usd": 0.01,
            },
            "elephant": {
                "runs": 1,
                "success_rate": 100.0,
                "avg_total_tokens": 9,
                "avg_latency_ms": 9,
                "total_cost_usd": 0.009,
            },
        },
    }
    report = benchmark_runner._build_report_md(payload)
    assert "- comparison_track: prompt-parity" in report
