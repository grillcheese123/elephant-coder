#!/usr/bin/env python3
"""Run capsule transport ablation: text vs hybrid vs capsule_only."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_multi(
    *,
    framework_root: Path,
    max_input_tokens: int,
    max_output_tokens: int,
    max_cost_usd: float,
    max_tasks: int,
    capsule_transport_enabled: str,
    capsule_transport_mode: str,
    capsule_transport_dim: int,
    capsule_transport_max_items: int,
    capsule_transport_fingerprint_bits: int,
) -> None:
    cmd = [
        "uv",
        "run",
        "--python",
        "3.12",
        "python",
        str(framework_root / "scripts" / "multi_fixture_benchmark_runner.py"),
        "--framework-root",
        str(framework_root),
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
        raise RuntimeError(f"multi_fixture_benchmark_runner failed (exit={result.returncode})")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _copy_variant_artifacts(framework_root: Path, variant: str, prefixes: list[str]) -> dict[str, Any]:
    runs = framework_root / ".elephant-coder" / "runs"
    out: dict[str, Any] = {"variant": variant, "fixtures": {}}
    for prefix in prefixes:
        result_src = runs / f"benchmark_results_{prefix}.json"
        report_src = runs / f"benchmark_report_{prefix}.md"
        summary_src = runs / f"{prefix}_summary.md"
        result_dst = runs / f"benchmark_results_{prefix}_{variant}.json"
        report_dst = runs / f"benchmark_report_{prefix}_{variant}.md"
        summary_dst = runs / f"{prefix}_summary_{variant}.md"
        if result_src.exists():
            shutil.copy2(result_src, result_dst)
            payload = _load_json(result_src)
            out["fixtures"][prefix] = payload
        if report_src.exists():
            shutil.copy2(report_src, report_dst)
        if summary_src.exists():
            shutil.copy2(summary_src, summary_dst)

    mf_src = runs / "multi_fixture_summary.md"
    mf_dst = runs / f"multi_fixture_summary_{variant}.md"
    if mf_src.exists():
        shutil.copy2(mf_src, mf_dst)
    return out


def _fixture_metrics(payload: dict[str, Any]) -> dict[str, float]:
    ag = payload.get("aggregates", {}) if isinstance(payload, dict) else {}
    base = ag.get("baseline", {}) if isinstance(ag, dict) else {}
    ele = ag.get("elephant", {}) if isinstance(ag, dict) else {}
    return {
        "token_reduction_pct": float(ag.get("token_reduction_pct", 0.0) or 0.0),
        "quality_delta_pct_points": float(ag.get("quality_delta_pct_points", 0.0) or 0.0),
        "latency_delta_ms": float(ag.get("latency_delta_ms", 0.0) or 0.0),
        "baseline_success_rate": float(base.get("success_rate", 0.0) or 0.0),
        "elephant_success_rate": float(ele.get("success_rate", 0.0) or 0.0),
        "baseline_avg_total_tokens": float(base.get("avg_total_tokens", 0.0) or 0.0),
        "elephant_avg_total_tokens": float(ele.get("avg_total_tokens", 0.0) or 0.0),
    }


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _write_report(path: Path, comparison: dict[str, Any]) -> None:
    rows = comparison.get("rows", [])
    lines: list[str] = []
    lines.append("# Capsule Transport Ablation Report")
    lines.append("")
    lines.append(f"- generated_at_utc: {comparison.get('generated_at_utc', '')}")
    lines.append(f"- task_mode: {comparison.get('task_mode', '')}")
    lines.append("")
    lines.append(
        "| fixture | text_token_reduction | hybrid_token_reduction | capsule_only_token_reduction | delta_hybrid_vs_text | delta_capsule_vs_text | delta_capsule_vs_hybrid | text_elephant_success | hybrid_elephant_success | capsule_elephant_success |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['fixture']} | {row['text_token_reduction_pct']:.2f} | "
            f"{row['hybrid_token_reduction_pct']:.2f} | {row['capsule_only_token_reduction_pct']:.2f} | "
            f"{row['delta_hybrid_vs_text_token_reduction_pct']:.2f} | "
            f"{row['delta_capsule_vs_text_token_reduction_pct']:.2f} | "
            f"{row['delta_capsule_vs_hybrid_token_reduction_pct']:.2f} | "
            f"{row['text_elephant_success_rate']:.2f} | {row['hybrid_elephant_success_rate']:.2f} | "
            f"{row['capsule_only_elephant_success_rate']:.2f} |"
        )
    lines.append("")
    avg = comparison.get("averages", {})
    lines.append("## Average Delta")
    lines.append(
        f"- delta_hybrid_vs_text_token_reduction_pct_mean: {float(avg.get('delta_hybrid_vs_text_token_reduction_pct_mean', 0.0)):.2f}"
    )
    lines.append(
        f"- delta_capsule_vs_text_token_reduction_pct_mean: {float(avg.get('delta_capsule_vs_text_token_reduction_pct_mean', 0.0)):.2f}"
    )
    lines.append(
        f"- delta_capsule_vs_hybrid_token_reduction_pct_mean: {float(avg.get('delta_capsule_vs_hybrid_token_reduction_pct_mean', 0.0)):.2f}"
    )
    lines.append(
        f"- delta_capsule_vs_text_elephant_success_rate_mean: {float(avg.get('delta_capsule_vs_text_elephant_success_rate_mean', 0.0)):.2f}"
    )
    lines.append(
        f"- delta_capsule_vs_hybrid_elephant_success_rate_mean: {float(avg.get('delta_capsule_vs_hybrid_elephant_success_rate_mean', 0.0)):.2f}"
    )
    lines.append(
        f"- delta_capsule_vs_text_elephant_avg_total_tokens_mean: {float(avg.get('delta_capsule_vs_text_elephant_avg_total_tokens_mean', 0.0)):.2f}"
    )
    lines.append(
        f"- delta_capsule_vs_hybrid_elephant_avg_total_tokens_mean: {float(avg.get('delta_capsule_vs_hybrid_elephant_avg_total_tokens_mean', 0.0)):.2f}"
    )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run capsule transport ablation (text vs hybrid vs capsule_only)"
    )
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
        "--capsule-mode",
        choices=["hybrid", "capsule_only"],
        default="capsule_only",
        help="Deprecated compatibility flag. Both hybrid and capsule_only are always run.",
    )
    parser.add_argument("--capsule-dim", type=int, default=768)
    parser.add_argument("--capsule-max-items", type=int, default=48)
    parser.add_argument("--capsule-fingerprint-bits", type=int, default=96)
    args = parser.parse_args()

    framework_root = Path(args.framework_root).resolve()
    prefixes = [
        "dummy_oop",
        "dummy_event_mesh",
        "dummy_policy_engine",
        "dummy_layered_inheritance",
        "dummy_cross_module",
    ]

    _run_multi(
        framework_root=framework_root,
        max_input_tokens=int(args.max_input_tokens),
        max_output_tokens=int(args.max_output_tokens),
        max_cost_usd=float(args.max_cost_usd),
        max_tasks=int(args.max_tasks),
        capsule_transport_enabled="false",
        capsule_transport_mode="hybrid",
        capsule_transport_dim=int(args.capsule_dim),
        capsule_transport_max_items=int(args.capsule_max_items),
        capsule_transport_fingerprint_bits=int(args.capsule_fingerprint_bits),
    )
    text_payload = _copy_variant_artifacts(framework_root, "text", prefixes)

    _run_multi(
        framework_root=framework_root,
        max_input_tokens=int(args.max_input_tokens),
        max_output_tokens=int(args.max_output_tokens),
        max_cost_usd=float(args.max_cost_usd),
        max_tasks=int(args.max_tasks),
        capsule_transport_enabled="true",
        capsule_transport_mode="hybrid",
        capsule_transport_dim=int(args.capsule_dim),
        capsule_transport_max_items=int(args.capsule_max_items),
        capsule_transport_fingerprint_bits=int(args.capsule_fingerprint_bits),
    )
    hybrid_payload = _copy_variant_artifacts(framework_root, "hybrid", prefixes)

    _run_multi(
        framework_root=framework_root,
        max_input_tokens=int(args.max_input_tokens),
        max_output_tokens=int(args.max_output_tokens),
        max_cost_usd=float(args.max_cost_usd),
        max_tasks=int(args.max_tasks),
        capsule_transport_enabled="true",
        capsule_transport_mode="capsule_only",
        capsule_transport_dim=int(args.capsule_dim),
        capsule_transport_max_items=int(args.capsule_max_items),
        capsule_transport_fingerprint_bits=int(args.capsule_fingerprint_bits),
    )
    capsule_payload = _copy_variant_artifacts(framework_root, "capsule_only", prefixes)

    rows: list[dict[str, Any]] = []
    for prefix in prefixes:
        text_fix = text_payload.get("fixtures", {}).get(prefix, {})
        hybrid_fix = hybrid_payload.get("fixtures", {}).get(prefix, {})
        capsule_fix = capsule_payload.get("fixtures", {}).get(prefix, {})
        t = _fixture_metrics(text_fix)
        h = _fixture_metrics(hybrid_fix)
        c = _fixture_metrics(capsule_fix)
        rows.append(
            {
                "fixture": prefix,
                "text_token_reduction_pct": t["token_reduction_pct"],
                "hybrid_token_reduction_pct": h["token_reduction_pct"],
                "capsule_only_token_reduction_pct": c["token_reduction_pct"],
                "delta_hybrid_vs_text_token_reduction_pct": h["token_reduction_pct"]
                - t["token_reduction_pct"],
                "delta_capsule_vs_text_token_reduction_pct": c["token_reduction_pct"]
                - t["token_reduction_pct"],
                "delta_capsule_vs_hybrid_token_reduction_pct": c["token_reduction_pct"]
                - h["token_reduction_pct"],
                "text_elephant_success_rate": t["elephant_success_rate"],
                "hybrid_elephant_success_rate": h["elephant_success_rate"],
                "capsule_only_elephant_success_rate": c["elephant_success_rate"],
                "delta_hybrid_vs_text_elephant_success_rate": h["elephant_success_rate"]
                - t["elephant_success_rate"],
                "delta_capsule_vs_text_elephant_success_rate": c["elephant_success_rate"]
                - t["elephant_success_rate"],
                "delta_capsule_vs_hybrid_elephant_success_rate": c["elephant_success_rate"]
                - h["elephant_success_rate"],
                "text_elephant_avg_total_tokens": t["elephant_avg_total_tokens"],
                "hybrid_elephant_avg_total_tokens": h["elephant_avg_total_tokens"],
                "capsule_only_elephant_avg_total_tokens": c["elephant_avg_total_tokens"],
                "delta_hybrid_vs_text_elephant_avg_total_tokens": h["elephant_avg_total_tokens"]
                - t["elephant_avg_total_tokens"],
                "delta_capsule_vs_text_elephant_avg_total_tokens": c["elephant_avg_total_tokens"]
                - t["elephant_avg_total_tokens"],
                "delta_capsule_vs_hybrid_elephant_avg_total_tokens": c["elephant_avg_total_tokens"]
                - h["elephant_avg_total_tokens"],
            }
        )

    averages = {
        "delta_hybrid_vs_text_token_reduction_pct_mean": _mean(
            [float(item["delta_hybrid_vs_text_token_reduction_pct"]) for item in rows]
        ),
        "delta_capsule_vs_text_token_reduction_pct_mean": _mean(
            [float(item["delta_capsule_vs_text_token_reduction_pct"]) for item in rows]
        ),
        "delta_capsule_vs_hybrid_token_reduction_pct_mean": _mean(
            [float(item["delta_capsule_vs_hybrid_token_reduction_pct"]) for item in rows]
        ),
        "delta_capsule_vs_text_elephant_success_rate_mean": _mean(
            [float(item["delta_capsule_vs_text_elephant_success_rate"]) for item in rows]
        ),
        "delta_capsule_vs_hybrid_elephant_success_rate_mean": _mean(
            [float(item["delta_capsule_vs_hybrid_elephant_success_rate"]) for item in rows]
        ),
        "delta_capsule_vs_text_elephant_avg_total_tokens_mean": _mean(
            [float(item["delta_capsule_vs_text_elephant_avg_total_tokens"]) for item in rows]
        ),
        "delta_capsule_vs_hybrid_elephant_avg_total_tokens_mean": _mean(
            [float(item["delta_capsule_vs_hybrid_elephant_avg_total_tokens"]) for item in rows]
        ),
        "delta_token_reduction_pct_mean": _mean(
            [float(item["delta_capsule_vs_text_token_reduction_pct"]) for item in rows]
        ),
        "delta_elephant_success_rate_mean": _mean(
            [float(item["delta_capsule_vs_text_elephant_success_rate"]) for item in rows]
        ),
        "delta_elephant_avg_total_tokens_mean": _mean(
            [float(item["delta_capsule_vs_text_elephant_avg_total_tokens"]) for item in rows]
        ),
    }

    comparison = {
        "generated_at_utc": _utc_now(),
        "task_mode": "same fixtures/tasks, same budgets; arms=text,hybrid,capsule_only",
        "rows": rows,
        "averages": averages,
    }

    runs = framework_root / ".elephant-coder" / "runs"
    json_path = runs / "capsule_transport_ablation_results.json"
    md_path = runs / "capsule_transport_ablation_report.md"
    json_path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    _write_report(md_path, comparison)
    print(json.dumps({"results_json": str(json_path), "report_md": str(md_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
