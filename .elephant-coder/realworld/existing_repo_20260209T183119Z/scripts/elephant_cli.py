#!/usr/bin/env python3
"""Elephant Coder CLI scaffold (Phase 1).

This module provides the command router, response envelope, project-local
layout bootstrap, config loading, and placeholder command handlers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import shlex
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_ROOT = Path(__file__).resolve().parents[1]

COMMANDS = ("plan", "code", "agents", "persona", "plugins", "git", "stats", "test", "session")
ERROR_CODES = {
    "E_CONFIG",
    "E_BUDGET",
    "E_MODEL",
    "E_INDEX",
    "E_IMPACT",
    "E_PLUGIN_PERMISSION",
    "E_STORAGE",
    "E_TEST",
}


@dataclass(frozen=True)
class RuntimeConfig:
    """Runtime configuration after defaults, file config, and CLI overrides."""

    output: str
    default_model: str
    model_fallbacks: tuple[str, ...]
    model_max_retries: int
    model_retry_backoff_sec: float
    max_input_tokens: int
    max_output_tokens: int
    max_cost_usd: float


class CLIError(RuntimeError):
    """Known CLI-level exception with stable error code."""

    def __init__(self, code: str, message: str):
        if code not in ERROR_CODES:
            raise ValueError(f"Unknown CLI error code: {code}")
        super().__init__(message)
        self.code = code
        self.message = message


def _utc_now_iso() -> str:
    """Return UTC timestamp in RFC3339-like format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_id(prefix: str) -> str:
    """Build a short deterministic-looking run/session ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _normalize_argv(argv: list[str]) -> list[str]:
    """Map slash commands to argparse command names."""
    if not argv:
        return argv
    if argv[0].startswith("/") and len(argv[0]) > 1:
        argv = [argv[0][1:]] + argv[1:]
    return argv


def _parse_scalar(value: str) -> Any:
    """Parse scalar config values from text."""
    raw = value.strip()
    low = raw.lower()
    if low in {"true", "false"}:
        return low == "true"
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        pass
    if "," in raw:
        return [part.strip() for part in raw.split(",") if part.strip()]
    return raw


def _default_config_map() -> dict[str, Any]:
    """Return flat default config values."""
    return {
        "output.default": "text",
        "model.default": "gpt-4o-mini",
        "model.fallbacks": [],
        "model.max_retries": 2,
        "model.retry_backoff_sec": 1.0,
        "budgets.max_input_tokens": 12000,
        "budgets.max_output_tokens": 3000,
        "budgets.max_cost_usd": 1.0,
        "plugins.allowed_permissions": [],
        "cognition.world_model.enabled": True,
        "cognition.world_model.dim": 512,
        "cognition.world_model.capsule_dim": 32,
        "cognition.world_model.semantic_dims": 28,
        "cognition.world_model.max_edge_facts": 20000,
        "cognition.world_model.max_symbol_facts": 5000,
    }


def _gguf_registry_path(project_root: Path) -> Path:
    """Return path to local GGUF specialist registry."""
    return project_root / ".elephant-coder" / "gguf_specialists.json"


def _default_gguf_registry() -> dict[str, Any]:
    """Return default GGUF specialist registry scaffold."""
    return {
        "version": 1,
        "specialists": [
            {
                "id": "planner_local",
                "role": "planner",
                "enabled": False,
                "backend": "llama_cpp_cli",
                "binary": "llama-cli",
                "model_path": "",
                "args": [],
            },
            {
                "id": "patcher_local",
                "role": "patcher",
                "enabled": False,
                "backend": "llama_cpp_cli",
                "binary": "llama-cli",
                "model_path": "",
                "args": [],
            },
            {
                "id": "reviewer_local",
                "role": "reviewer",
                "enabled": False,
                "backend": "llama_cpp_cli",
                "binary": "llama-cli",
                "model_path": "",
                "args": [],
            },
        ],
    }


def _load_gguf_registry(project_root: Path) -> dict[str, Any]:
    """Load GGUF registry from disk with safe defaults."""
    path = _gguf_registry_path(project_root)
    if not path.exists():
        return _default_gguf_registry()
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return _default_gguf_registry()
    if not isinstance(payload, dict):
        return _default_gguf_registry()
    specialists = payload.get("specialists", [])
    if not isinstance(specialists, list):
        specialists = []
    return {
        "version": int(payload.get("version", 1) or 1),
        "specialists": [item for item in specialists if isinstance(item, dict)],
    }


def _specialist_ready(spec: dict[str, Any]) -> tuple[bool, str]:
    """Check whether a specialist appears runnable."""
    if not bool(spec.get("enabled", False)):
        return False, "disabled"
    backend = str(spec.get("backend", "llama_cpp_cli")).strip().lower()
    if backend == "openrouter":
        model = str(spec.get("model", "") or spec.get("openrouter_model", "")).strip()
        if not model:
            return False, "missing model"
        return True, "ready"
    if backend == "llama_cpp_cli":
        model_path = str(spec.get("model_path", "")).strip()
        if not model_path:
            return False, "missing model_path"
        if not Path(model_path).exists():
            return False, "model file not found"
        binary = str(spec.get("binary", "")).strip() or "llama-cli"
        if shutil.which(binary) is None:
            return False, f"binary not found: {binary}"
        return True, "ready"
    return False, f"unsupported backend: {backend}"


def _normalized_specialists(project_root: Path) -> list[dict[str, Any]]:
    """Return normalized specialist entries with readiness metadata."""
    out: list[dict[str, Any]] = []
    for item in _load_gguf_registry(project_root).get("specialists", []):
        sid = str(item.get("id", "")).strip()
        role = str(item.get("role", "")).strip()
        if not sid:
            continue
        enabled = bool(item.get("enabled", False))
        ready, reason = _specialist_ready(item)
        model = str(item.get("model", "") or item.get("openrouter_model", "")).strip()
        out.append(
            {
                "id": sid,
                "role": role or "generalist",
                "enabled": enabled,
                "backend": str(item.get("backend", "llama_cpp_cli")),
                "binary": str(item.get("binary", "llama-cli")),
                "model": model,
                "model_path": str(item.get("model_path", "")),
                "args": item.get("args", []) if isinstance(item.get("args", []), list) else [],
                "ready": ready,
                "ready_reason": reason,
            }
        )
    return out


def _select_local_specialist(
    project_root: Path,
    task: str,
    requested: str | None,
) -> tuple[dict[str, Any] | None, str]:
    """Pick a local specialist by explicit request or simple task heuristic."""
    specialists = _normalized_specialists(project_root)
    if not specialists:
        return None, "no local specialists configured"

    if requested:
        needle = requested.strip().lower()
        for spec in specialists:
            if spec["id"].lower() == needle or str(spec["role"]).lower() == needle:
                return spec, "requested specialist"
        return None, f"requested specialist not found: {requested}"

    low_task = task.lower()
    wanted_role = "patcher"
    if any(tok in low_task for tok in ("plan", "roadmap", "milestone", "architecture")):
        wanted_role = "planner"
    elif any(tok in low_task for tok in ("test", "verify", "review", "audit")):
        wanted_role = "reviewer"

    for spec in specialists:
        if str(spec.get("role", "")).lower() == wanted_role:
            return spec, f"task-heuristic role={wanted_role}"
    for spec in specialists:
        if bool(spec.get("enabled", False)):
            return spec, "first enabled specialist fallback"
    return specialists[0], "first specialist fallback"


def _route_for_code(
    *,
    project_root: Path,
    router_mode: str,
    task: str,
    requested_specialist: str | None,
) -> tuple[dict[str, Any], list[str]]:
    """Resolve route for /code between OpenRouter default and specialist runtimes."""
    warnings: list[str] = []
    mode = router_mode.strip().lower()
    if mode not in {"auto", "openrouter", "local"}:
        raise CLIError("E_CONFIG", f"Unsupported router mode: {router_mode}")

    selected, selection_reason = _select_local_specialist(project_root, task, requested_specialist)
    if mode == "openrouter":
        return {
            "route": "openrouter",
            "reason": "router=openrouter",
            "local_specialist": selected["id"] if selected else None,
            "selection_reason": selection_reason if selected else "n/a",
        }, warnings

    if mode == "local":
        if selected is None:
            raise CLIError("E_MODEL", f"Local routing requested but unavailable: {selection_reason}")
        if not bool(selected.get("ready", False)):
            raise CLIError(
                "E_MODEL",
                (
                    f"Local routing requested for specialist '{selected['id']}' "
                    f"but it is not ready ({selected.get('ready_reason', 'unknown')})."
                ),
            )
        return {
            "route": "local",
            "reason": "router=local",
            "local_specialist": selected["id"],
            "selection_reason": selection_reason,
        }, warnings

    if selected is not None and bool(selected.get("ready", False)):
        return {
            "route": "local",
            "reason": "auto selected ready local specialist",
            "local_specialist": selected["id"],
            "selection_reason": selection_reason,
        }, warnings

    if selected is not None and bool(selected.get("enabled", False)):
        warnings.append(
            "Local specialist was selected but not ready; falling back to OpenRouter "
            f"({selected.get('ready_reason', 'unknown')})."
        )
    return {
        "route": "openrouter",
        "reason": "auto fallback to openrouter",
        "local_specialist": selected["id"] if selected else None,
        "selection_reason": selection_reason,
    }, warnings


def _messages_to_local_prompt(messages: list[dict[str, str]]) -> str:
    """Serialize chat-style messages into one prompt string for local CLI runtimes."""
    blocks: list[str] = []
    for item in messages:
        role = str(item.get("role", "user")).upper()
        content = str(item.get("content", ""))
        blocks.append(f"[{role}]\n{content}")
    return "\n\n".join(blocks).strip() + "\n\n[ASSISTANT]\n"


def _run_local_specialist_inference(
    *,
    project_root: Path,
    spec: dict[str, Any],
    messages: list[dict[str, str]],
    max_tokens: int,
    timeout_sec: int = 120,
) -> tuple[str, dict[str, int], float]:
    """Run local GGUF specialist via llama.cpp CLI backend."""
    backend = str(spec.get("backend", "llama_cpp_cli")).strip().lower()
    if backend != "llama_cpp_cli":
        raise CLIError("E_MODEL", f"Unsupported local backend: {backend}")

    binary = str(spec.get("binary", "")).strip() or "llama-cli"
    model_path = str(spec.get("model_path", "")).strip()
    if shutil.which(binary) is None:
        raise CLIError("E_MODEL", f"Local backend binary not found: {binary}")
    if not model_path or not Path(model_path).exists():
        raise CLIError("E_MODEL", f"Local model file not found: {model_path}")

    prompt = _messages_to_local_prompt(messages)
    cache_dir = project_root / ".elephant-coder" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(cache_dir),
        suffix=".prompt.txt",
    ) as handle:
        handle.write(prompt)
        prompt_file = Path(handle.name)

    extra = [str(item) for item in spec.get("args", []) if str(item).strip()]
    cmd = [
        binary,
        "-m",
        model_path,
        "-f",
        str(prompt_file),
        "-n",
        str(max_tokens),
        "--temp",
        "0.2",
    ] + extra
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=timeout_sec,
        )
    except OSError as exc:
        raise CLIError("E_MODEL", f"Local specialist launch failed: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise CLIError("E_MODEL", f"Local specialist timed out: {exc}") from exc
    finally:
        try:
            prompt_file.unlink(missing_ok=True)
        except Exception:
            pass

    if result.returncode != 0:
        err = (result.stderr or "").strip().splitlines()
        tail = err[-1] if err else f"exit={result.returncode}"
        raise CLIError("E_MODEL", f"Local specialist failed: {tail}")

    content = (result.stdout or "").strip()
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    return content, usage, 0.0


def _default_elephant_root() -> Path:
    """Return the Elephant Coder project root (directory above scripts/)."""
    return Path(__file__).resolve().parents[1]


def detect_project_root(start_path: str | Path) -> Path:
    """Resolve project root, preferring Elephant Coder root.

    Priority:
    1. `ELEPHANT_PROJECT_ROOT` environment override.
    2. Elephant Coder default root (`private/models/elephant-coder`).
    3. Fallback walk-up from cwd to `.git` or `pyproject.toml`.
    """
    override = os.getenv("ELEPHANT_PROJECT_ROOT")
    if override:
        return Path(override).resolve()

    elephant_root = _default_elephant_root()
    if (elephant_root / "INSTRUCTIONS.md").exists():
        return elephant_root

    start = Path(start_path).resolve()
    if start.is_file():
        start = start.parent
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return start


def ensure_project_layout(project_root: Path) -> Path:
    """Create project-local Elephant Coder directories and defaults."""
    base = project_root / ".elephant-coder"
    for rel in ("runs", "sessions", "personas", "plugins", "cache", "checkpoints"):
        (base / rel).mkdir(parents=True, exist_ok=True)

    config_path = base / "config.md"
    if not config_path.exists():
        config_path.write_text(
            "\n".join(
                [
                    "# Elephant Coder Config",
                    "",
                    "output.default: text",
                    "model.default: gpt-4o-mini",
                    "model.fallbacks: ",
                    "model.max_retries: 2",
                    "model.retry_backoff_sec: 1.0",
                    "budgets.max_input_tokens: 12000",
                    "budgets.max_output_tokens: 3000",
                    "budgets.max_cost_usd: 1.0",
                    "cognition.world_model.enabled: true",
                    "cognition.world_model.dim: 512",
                    "cognition.world_model.capsule_dim: 32",
                    "cognition.world_model.semantic_dims: 28",
                    "cognition.world_model.max_edge_facts: 20000",
                    "cognition.world_model.max_symbol_facts: 5000",
                    "plugins.allowed_permissions: read_fs",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    default_persona = base / "personas" / "default.md"
    if not default_persona.exists():
        default_persona.write_text(
            "\n".join(
                [
                    "# Default Persona",
                    "",
                    "## Goals",
                    "- Minimize token usage.",
                    "- Prefer precise changes and constrained context.",
                    "",
                    "## Behavior",
                    "- concise",
                    "- deterministic",
                    "- budget-aware",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    gguf_registry = _gguf_registry_path(project_root)
    if not gguf_registry.exists():
        gguf_registry.write_text(
            json.dumps(_default_gguf_registry(), indent=2) + "\n",
            encoding="utf-8",
        )
    return base


def load_config(project_root: Path) -> dict[str, Any]:
    """Load config from .elephant-coder/config.md into a flat map."""
    config = _default_config_map()
    cfg = project_root / ".elephant-coder" / "config.md"
    if not cfg.exists():
        return config

    for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
        striped = line.strip()
        if not striped or striped.startswith("#") or ":" not in striped:
            continue
        key, raw = striped.split(":", 1)
        key = key.strip()
        if not key:
            continue
        config[key] = _parse_scalar(raw)
    return config


def resolve_runtime_config(args: argparse.Namespace, config: dict[str, Any]) -> RuntimeConfig:
    """Resolve runtime config with CLI overrides taking precedence."""
    output = args.output or str(config.get("output.default", "text"))
    model = str(config.get("model.default", "gpt-4o-mini"))
    raw_fallbacks = config.get("model.fallbacks", [])
    if isinstance(raw_fallbacks, str):
        fallback_list = [item.strip() for item in raw_fallbacks.split(",") if item.strip()]
    elif isinstance(raw_fallbacks, list):
        fallback_list = [str(item).strip() for item in raw_fallbacks if str(item).strip()]
    else:
        fallback_list = []
    model_fallbacks = tuple(item for item in fallback_list if item != model)
    model_max_retries = max(0, int(config.get("model.max_retries", 2)))
    model_retry_backoff_sec = max(0.0, float(config.get("model.retry_backoff_sec", 1.0)))

    max_input = int(
        args.max_input_tokens
        if args.max_input_tokens is not None
        else config.get("budgets.max_input_tokens", 12000)
    )
    max_output = int(
        args.max_output_tokens
        if args.max_output_tokens is not None
        else config.get("budgets.max_output_tokens", 3000)
    )
    max_cost = float(
        args.max_cost_usd
        if args.max_cost_usd is not None
        else config.get("budgets.max_cost_usd", 1.0)
    )
    return RuntimeConfig(
        output=output,
        default_model=model,
        model_fallbacks=model_fallbacks,
        model_max_retries=model_max_retries,
        model_retry_backoff_sec=model_retry_backoff_sec,
        max_input_tokens=max_input,
        max_output_tokens=max_output,
        max_cost_usd=max_cost,
    )


def _build_response(
    *,
    ok: bool,
    command: str,
    run_id: str,
    session_id: str,
    data: dict[str, Any],
    warnings: list[str],
    errors: list[dict[str, str]],
    latency_ms: int,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a response envelope matching the v1 spec."""
    merged_metrics = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "latency_ms": latency_ms,
    }
    if metrics:
        for key in ("input_tokens", "output_tokens", "total_tokens", "estimated_cost_usd"):
            if key in metrics:
                merged_metrics[key] = metrics[key]
        merged_metrics["latency_ms"] = latency_ms

    return {
        "ok": ok,
        "command": command,
        "run_id": run_id,
        "session_id": session_id,
        "data": data,
        "metrics": merged_metrics,
        "warnings": warnings,
        "errors": errors,
    }


def _write_run_record(base: Path, response: dict[str, Any]) -> None:
    """Persist run response to project-local run records."""
    run_file = base / "runs" / f"{response['run_id']}.json"
    run_file.write_text(json.dumps(response, indent=2), encoding="utf-8")


def _session_log_path(project_root: Path, session_id: str) -> Path:
    """Return JSONL path for one session log."""
    safe = "".join(ch for ch in session_id if ch.isalnum() or ch in {"-", "_"})
    safe = safe or "session"
    return project_root / ".elephant-coder" / "sessions" / f"{safe}.jsonl"


def _append_session_event(
    project_root: Path,
    session_id: str,
    role: str,
    content: str,
    *,
    command: str = "/code",
    run_id: str | None = None,
) -> None:
    """Append one session event line."""
    if not session_id or not content.strip():
        return
    path = _session_log_path(project_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": _utc_now_iso(),
        "session_id": session_id,
        "role": role,
        "command": command,
        "run_id": run_id,
        "content": content.strip(),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def _load_session_context(
    project_root: Path,
    session_id: str,
    *,
    max_events: int = 10,
    max_chars: int = 2500,
) -> tuple[str, dict[str, Any]]:
    """Load compact session context text for model prompts."""
    if not session_id:
        return "(no session id)", {"events": 0, "truncated": False}
    path = _session_log_path(project_root, session_id)
    if not path.exists():
        return "(no prior session context)", {"events": 0, "truncated": False}

    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            item = json.loads(raw)
        except Exception:
            continue
        if isinstance(item, dict):
            events.append(item)

    recent = events[-max_events:]
    lines: list[str] = []
    for item in recent:
        role = str(item.get("role", "unknown"))
        content = str(item.get("content", "")).strip().replace("\n", " ")
        if len(content) > 280:
            content = content[:280] + "..."
        lines.append(f"- {role}: {content}")

    text = "\n".join(lines) if lines else "(no prior session context)"
    truncated = False
    if len(text) > max_chars:
        text = text[-max_chars:]
        truncated = True
    return text, {"events": len(recent), "truncated": truncated}


_PROMPT_INJECTION_PATTERNS = (
    "ignore previous",
    "ignore all previous",
    "forget",
    "override",
    "suspend",
    "jailbreak",
    "system prompt",
    "you wake up",
    "no instruction about the behavior",
)


def _active_persona_marker_path(project_root: Path) -> Path:
    """Return path for persisted active persona marker."""
    return project_root / ".elephant-coder" / "personas" / "active.txt"


def _prompt_library_index_path(project_root: Path) -> Path:
    """Return path for prompt-ingestion index file."""
    return project_root / ".elephant-coder" / "cache" / "prompt_library.json"


def _slugify_name(name: str) -> str:
    """Return lowercase slug for filenames."""
    raw = str(name or "").strip().lower()
    if not raw:
        return "persona"
    out: list[str] = []
    prev_dash = False
    for ch in raw:
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
            continue
        if not prev_dash:
            out.append("-")
            prev_dash = True
    slug = "".join(out).strip("-")
    return slug or "persona"


def _persona_file_from_name(name: str) -> str:
    """Normalize persona name to safe markdown filename."""
    raw = str(name or "").strip().replace("\\", "/")
    raw = raw.split("/")[-1]
    if raw.lower().endswith(".md"):
        raw = raw[:-3]
    return f"{_slugify_name(raw)}.md"


def _read_active_persona(project_root: Path, available: list[str]) -> str | None:
    """Read active persona marker if present and valid."""
    marker = _active_persona_marker_path(project_root)
    if not marker.exists():
        return None
    try:
        raw = marker.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    if not raw:
        return None
    candidate = _persona_file_from_name(raw)
    if candidate in available:
        return candidate
    return None


def _is_risky_prompt_line(text: str) -> bool:
    """Detect likely prompt-injection or instruction-override lines."""
    low = text.lower()
    return any(pattern in low for pattern in _PROMPT_INJECTION_PATTERNS)


def _classify_prompt_section(title: str) -> str:
    """Assign coarse section class from heading title."""
    low = title.strip().lower()
    if any(tok in low for tok in ("persona", "role", "team")):
        return "persona"
    if any(tok in low for tok in ("process", "step", "workflow", "protocol", "plan")):
        return "process"
    if any(tok in low for tok in ("style", "communication", "tone", "interaction")):
        return "style"
    if any(tok in low for tok in ("guideline", "rule", "principle", "constraint")):
        return "rules"
    if any(tok in low for tok in ("risk", "security", "safety", "edge case")):
        return "safety"
    return "general"


def _split_markdown_sections(text: str) -> list[dict[str, Any]]:
    """Split markdown text by headings and preserve line numbers."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    sections: list[dict[str, Any]] = []
    current = {"title": "Document", "level": 1, "lines": []}
    in_fence = False
    fence_marker = ""

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = "```" if stripped.startswith("```") else "~~~"
            if in_fence and marker == fence_marker:
                in_fence = False
                fence_marker = ""
            elif not in_fence:
                in_fence = True
                fence_marker = marker
            current["lines"].append((lineno, raw))
            continue

        if in_fence:
            current["lines"].append((lineno, raw))
            continue

        if stripped.startswith("#"):
            hashes = 0
            while hashes < len(stripped) and stripped[hashes] == "#":
                hashes += 1
            if hashes > 0 and (hashes == len(stripped) or stripped[hashes] == " "):
                if current["lines"]:
                    sections.append(current)
                heading = stripped[hashes:].strip() or "Untitled"
                current = {"title": heading, "level": hashes, "lines": []}
                continue
        current["lines"].append((lineno, raw))

    if current["lines"]:
        sections.append(current)
    return sections


def _build_persona_markdown(
    *,
    display_name: str,
    source_path: Path,
    sections: list[dict[str, Any]],
    max_sections: int = 12,
    max_lines_per_section: int = 16,
) -> str:
    """Build compact, sanitized persona markdown from classified sections."""
    priority = {"persona": 0, "process": 1, "style": 2, "rules": 3, "safety": 4, "general": 5}
    ranked = sorted(
        sections,
        key=lambda item: (priority.get(str(item.get("kind", "general")), 99), int(item["index"])),
    )

    chosen: list[dict[str, Any]] = []
    for section in ranked:
        safe_lines = section.get("safe_lines", [])
        if not isinstance(safe_lines, list) or not safe_lines:
            continue
        chosen.append(section)
        if len(chosen) >= max_sections:
            break

    out = [
        f"# {display_name}",
        "",
        "## Source",
        f"- prompt_file: {source_path.as_posix()}",
        f"- generated_at_utc: {_utc_now_iso()}",
        "",
        "## Extracted Guidance",
    ]
    if not chosen:
        out.extend(["- No safe guidance extracted.", ""])
        return "\n".join(out).rstrip() + "\n"

    for section in chosen:
        title = str(section.get("title", "Section")).strip() or "Section"
        out.append(f"### {title}")
        safe_lines = [str(item) for item in section.get("safe_lines", [])]
        kept = 0
        for line in safe_lines:
            if kept >= max_lines_per_section:
                break
            value = line.rstrip()
            if not value:
                if out and out[-1] != "":
                    out.append("")
                continue
            out.append(value)
            kept += 1
        if len(safe_lines) > kept:
            out.append("... (truncated)")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _load_prompt_library_index(project_root: Path) -> dict[str, Any]:
    """Load prompt library index, creating default shape when missing."""
    path = _prompt_library_index_path(project_root)
    if not path.exists():
        return {"version": 1, "items": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {"version": 1, "items": []}
    if not isinstance(payload, dict):
        return {"version": 1, "items": []}
    items = payload.get("items", [])
    if not isinstance(items, list):
        items = []
    return {"version": 1, "items": [item for item in items if isinstance(item, dict)]}


def _upsert_prompt_library_index(project_root: Path, entry: dict[str, Any]) -> None:
    """Insert or replace one prompt-ingestion entry."""
    index = _load_prompt_library_index(project_root)
    items = list(index.get("items", []))
    persona_file = str(entry.get("persona_file", ""))
    items = [item for item in items if str(item.get("persona_file", "")) != persona_file]
    items.insert(0, entry)
    index["items"] = items[:200]
    path = _prompt_library_index_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def _ingest_prompt_markdown_file(
    *,
    project_root: Path,
    source_path: str,
    store_name: str | None,
    activate: bool,
) -> dict[str, Any]:
    """Ingest markdown prompt file and persist compact persona assets."""
    src = Path(source_path).expanduser()
    if not src.is_absolute():
        src = (project_root / src).resolve()
    else:
        src = src.resolve()
    if not src.exists() or not src.is_file():
        raise CLIError("E_STORAGE", f"Prompt source file not found: {source_path}")

    try:
        raw_text = src.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise CLIError("E_STORAGE", f"Unable to read prompt source: {exc}") from exc

    sections_raw = _split_markdown_sections(raw_text)
    classified: list[dict[str, Any]] = []
    flagged_lines: list[dict[str, Any]] = []
    kept_lines_total = 0
    dropped_lines_total = 0
    for index, section in enumerate(sections_raw):
        safe_lines: list[str] = []
        risky_count = 0
        for line_no, raw in section.get("lines", []):
            normalized = (
                str(raw)
                .replace("\t", "    ")
                .replace("\u2013", "-")
                .replace("\u2014", "-")
                .rstrip()
            )
            ascii_line = normalized.encode("ascii", errors="ignore").decode("ascii")
            if _is_risky_prompt_line(ascii_line):
                risky_count += 1
                dropped_lines_total += 1
                if len(flagged_lines) < 32:
                    flagged_lines.append(
                        {
                            "line": int(line_no),
                            "section": str(section.get("title", "")),
                            "text": ascii_line[:180],
                        }
                    )
                continue
            if ascii_line.strip():
                safe_lines.append(ascii_line)
                kept_lines_total += 1
            elif safe_lines and safe_lines[-1] != "":
                safe_lines.append("")

        while safe_lines and not safe_lines[-1]:
            safe_lines.pop()
        kind = _classify_prompt_section(str(section.get("title", "")))
        classified.append(
            {
                "index": index,
                "title": str(section.get("title", "Section")),
                "kind": kind,
                "safe_lines": safe_lines,
                "risky_lines": risky_count,
            }
        )

    source_hash = hashlib.sha256(raw_text.encode("utf-8", errors="replace")).hexdigest()
    display_name = (store_name or src.stem).strip() or "Persona"
    slug = _slugify_name(display_name)
    persona_file = f"{slug}.md"
    meta_file = f"{slug}.meta.json"
    personas_dir = project_root / ".elephant-coder" / "personas"
    persona_path = personas_dir / persona_file
    meta_path = personas_dir / meta_file

    persona_markdown = _build_persona_markdown(
        display_name=display_name,
        source_path=src,
        sections=classified,
    )
    _write_text_if_changed(persona_path, persona_markdown)
    meta_payload = {
        "schema_version": 1,
        "display_name": display_name,
        "persona_file": persona_file,
        "source_path": src.as_posix(),
        "source_sha256": source_hash,
        "ingested_at_utc": _utc_now_iso(),
        "sections_total": len(classified),
        "safe_sections": sum(1 for item in classified if item.get("safe_lines")),
        "kept_lines_total": kept_lines_total,
        "dropped_lines_total": dropped_lines_total,
        "flagged_lines": flagged_lines,
        "sections": [
            {
                "title": str(item["title"]),
                "kind": str(item["kind"]),
                "safe_lines": len(item["safe_lines"]),
                "risky_lines": int(item["risky_lines"]),
            }
            for item in classified
        ],
    }
    meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

    _upsert_prompt_library_index(
        project_root,
        {
            "persona_file": persona_file,
            "meta_file": meta_file,
            "display_name": display_name,
            "source_path": src.as_posix(),
            "source_sha256": source_hash,
            "ingested_at_utc": meta_payload["ingested_at_utc"],
            "sections_total": meta_payload["sections_total"],
            "safe_sections": meta_payload["safe_sections"],
            "dropped_lines_total": dropped_lines_total,
        },
    )

    if activate:
        _write_text_if_changed(_active_persona_marker_path(project_root), persona_file + "\n")

    return {
        "persona_file": persona_file,
        "meta_file": meta_file,
        "source_path": src.as_posix(),
        "source_sha256": source_hash,
        "sections_total": meta_payload["sections_total"],
        "safe_sections": meta_payload["safe_sections"],
        "flagged_lines_count": len(flagged_lines),
        "activate_applied": activate,
    }


def _load_persona_guidance(
    project_root: Path,
    requested_persona: str | None,
    *,
    max_chars: int = 2600,
) -> tuple[str | None, str, dict[str, Any], list[str]]:
    """Load active persona markdown snippet for /code prompts."""
    personas_dir = project_root / ".elephant-coder" / "personas"
    available = sorted(path.name for path in personas_dir.glob("*.md"))
    warnings: list[str] = []

    active: str | None = None
    if requested_persona:
        candidate = _persona_file_from_name(requested_persona)
        if candidate in available:
            active = candidate
        else:
            warnings.append(f"Requested persona '{requested_persona}' was not found; using default.")
    if active is None:
        marker = _read_active_persona(project_root, available)
        if marker:
            active = marker
    if active is None and "default.md" in available:
        active = "default.md"
    if active is None and available:
        active = available[0]

    if not active:
        return None, "", {"active_persona": None, "available_personas": available, "truncated": False}, warnings

    path = personas_dir / active
    try:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return active, "", {"active_persona": active, "available_personas": available, "truncated": False}, warnings

    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n... (truncated)"
        truncated = True
    meta = {
        "active_persona": active,
        "available_personas": available,
        "truncated": truncated,
        "chars": len(text),
    }
    return active, text, meta, warnings


def _dedupe_lines(items: list[str]) -> list[str]:
    """Deduplicate strings while preserving order."""
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _persona_plan_signals(persona_text: str) -> dict[str, bool]:
    """Infer planning priorities from persona guidance text."""
    low = str(persona_text or "").lower()
    return {
        "timeline": any(tok in low for tok in ("timeline", "milestone", "deadline", "schedule")),
        "dependencies": any(
            tok in low for tok in ("dependency", "dependencies", "critical path", "sequencing")
        ),
        "risk_management": any(tok in low for tok in ("risk", "mitigation", "blocker")),
        "stakeholder_alignment": any(
            tok in low for tok in ("stakeholder", "communication", "status update", "alignment")
        ),
        "acceptance_criteria": any(
            tok in low for tok in ("acceptance", "definition of done", "success criteria", "validation")
        ),
    }


def _persona_plan_adjustments(persona_text: str) -> dict[str, Any]:
    """Return persona-driven planning overlays for /plan."""
    signals = _persona_plan_signals(persona_text)
    steps: list[str] = []
    assumptions: list[str] = []
    risks: list[str] = []

    if persona_text.strip():
        steps.append("Apply active persona planning constraints before finalizing task sequence.")
    if signals["timeline"]:
        steps.append("Define milestones/checkpoints and estimate delivery order by impact.")
    if signals["dependencies"]:
        steps.append("Capture dependency chain and critical path across impacted files.")
    if signals["risk_management"]:
        steps.append("Create a risk register with mitigations for high-impact changes.")
        risks.append("Execution risk should be tracked explicitly with mitigation owners.")
    if signals["stakeholder_alignment"]:
        steps.append("Prepare stakeholder update checkpoints tied to implementation milestones.")
        assumptions.append("Stakeholder communication cadence is part of plan deliverables.")
    if signals["acceptance_criteria"]:
        steps.append("Define acceptance criteria and verification checkpoints for each milestone.")
        assumptions.append("Plan completeness requires explicit acceptance criteria.")

    return {
        "signals": signals,
        "plan_steps": _dedupe_lines(steps),
        "assumptions": _dedupe_lines(assumptions),
        "risks": _dedupe_lines(risks),
    }


def _numbered_lines(items: list[str]) -> list[str]:
    """Return markdown numbered lines from a list of strings."""
    out: list[str] = []
    for idx, item in enumerate(items, start=1):
        out.append(f"{idx}. {item}")
    return out


def _build_plan_markdown(
    *,
    task: str,
    active_persona: str | None,
    cot_steps: list[str],
    plan_steps: list[str],
    assumptions: list[str],
    risks: list[str],
    impacted_files: list[str],
    persona_signals: dict[str, bool],
    index_stats: dict[str, Any],
    impact_report: dict[str, Any],
) -> str:
    """Build PLAN.md markdown content for /plan output."""
    lines: list[str] = []
    lines.append("# PLAN")
    lines.append("")
    lines.append("## Context")
    lines.append(f"- generated_at_utc: {_utc_now_iso()}")
    lines.append(f"- task: {task}")
    lines.append(f"- active_persona: {active_persona or 'none'}")
    lines.append("")
    lines.append("## Chain of Thought (Structured)")
    lines.extend(_numbered_lines(cot_steps))
    lines.append("")
    lines.append("## Execution Steps")
    lines.extend(_numbered_lines(plan_steps))
    lines.append("")
    lines.append("## Assumptions")
    if assumptions:
        lines.extend(f"- {item}" for item in assumptions)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Risks")
    if risks:
        lines.extend(f"- {item}" for item in risks)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Impacted Files")
    if impacted_files:
        lines.extend(f"- {item}" for item in impacted_files)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Persona Signals")
    for key in sorted(persona_signals):
        lines.append(f"- {key}: {bool(persona_signals[key])}")
    lines.append("")
    lines.append("## Index Summary")
    lines.append(f"- files_scanned: {int(index_stats.get('files_scanned', 0))}")
    lines.append(f"- edges_total: {int(index_stats.get('edges_total', 0))}")
    lines.append(f"- parse_errors: {int(index_stats.get('parse_errors', 0))}")
    lines.append("")
    lines.append("## Impact Summary")
    lines.append(f"- direct_count: {int(impact_report.get('direct_count', 0))}")
    lines.append(f"- transitive_count: {int(impact_report.get('transitive_count', 0))}")
    lines.append(f"- max_depth: {int(impact_report.get('max_depth', 0))}")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _git_status(project_root: Path) -> tuple[str, list[str], str | None]:
    """Return git short status text and changed files."""
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "status", "--short"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return "", [], f"git not available: {exc}"

    if result.returncode != 0:
        return "", [], result.stderr.strip() or "git status failed"

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    changed = []
    for line in lines:
        if len(line) > 3:
            changed.append(line[3:].strip())
    return "\n".join(lines), changed, None


def _normalize_changed_path(raw: str, project_root: Path) -> str | None:
    """Normalize changed path from git output to project-relative POSIX."""
    item = str(raw).strip()
    if " -> " in item:
        item = item.split(" -> ", 1)[1].strip()
    item = item.replace("\\", "/")
    if not item:
        return None
    path = Path(item)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(project_root.resolve()).as_posix()
        except ValueError:
            return None
    candidate = (project_root / path).resolve()
    try:
        return candidate.relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return None


def _changed_python_files(project_root: Path, changed: list[str]) -> list[str]:
    """Return normalized changed Python files only."""
    out: set[str] = set()
    for item in changed:
        norm = _normalize_changed_path(item, project_root)
        if norm and norm.endswith(".py"):
            out.add(norm)
    return sorted(out)


def _get_elephant_exports():
    """Load Elephant package exports with script-path fallback."""
    try:
        from elephant_coder import (  # type: ignore[import-not-found]
            IndexService,
            OpenRouterClient,
            OpenRouterError,
            load_dotenv,
        )
        return IndexService, OpenRouterClient, OpenRouterError, load_dotenv
    except (ModuleNotFoundError, ImportError):
        if str(_SCRIPT_ROOT) not in sys.path:
            sys.path.insert(0, str(_SCRIPT_ROOT))
        try:
            from elephant_coder import (  # type: ignore[import-not-found]
                IndexService,
                OpenRouterClient,
                OpenRouterError,
                load_dotenv,
            )
            return IndexService, OpenRouterClient, OpenRouterError, load_dotenv
        except (ModuleNotFoundError, ImportError):
            from elephant_coder.env_utils import load_dotenv  # type: ignore[import-not-found]
            from elephant_coder.index_engine import IndexService  # type: ignore[import-not-found]
            from elephant_coder.openrouter_client import (  # type: ignore[import-not-found]
                OpenRouterClient,
                OpenRouterError,
            )

            return IndexService, OpenRouterClient, OpenRouterError, load_dotenv


def _new_index_service(project_root: Path):
    """Create index service, with local import fallback for script execution."""
    config = load_config(project_root)
    index_service_cls, _, _, _ = _get_elephant_exports()
    return index_service_cls(
        project_root,
        world_model_enabled=bool(config.get("cognition.world_model.enabled", True)),
        world_model_dim=int(config.get("cognition.world_model.dim", 512) or 512),
        world_model_capsule_dim=int(config.get("cognition.world_model.capsule_dim", 32) or 32),
        world_model_semantic_dims=int(config.get("cognition.world_model.semantic_dims", 28) or 28),
        world_model_max_edge_facts=int(
            config.get("cognition.world_model.max_edge_facts", 20000) or 20000
        ),
        world_model_max_symbol_facts=int(
            config.get("cognition.world_model.max_symbol_facts", 5000) or 5000
        ),
    )


def _new_openrouter_client(api_key: str):
    """Create OpenRouter client with fallback imports."""
    _, openrouter_client_cls, _, _ = _get_elephant_exports()
    return openrouter_client_cls(api_key, app_name="elephant-coder")


def _build_code_messages(
    *,
    task: str,
    context_text: str,
    persona_text: str = "",
) -> list[dict[str, str]]:
    """Build compact prompt messages for a single coding worker."""
    system = (
        "You are a coding worker agent. Optimize for minimal-token, high-precision output.\n"
        "Use all provided context modalities (code chunks, AST/graph features, git diff, runtime traces).\n"
        "Return STRICT JSON only (no markdown fences) with this shape:\n"
        "{"
        "\"summary\": str, "
        "\"project\": {\"language\": str}, "
        "\"files\": [{\"path\": str, \"content\": str}], "
        "\"dependencies\": {"
        "\"dependencies\": {name: version}, "
        "\"devDependencies\": {name: version}, "
        "\"python\": [\"pkg==ver\"], "
        "\"pythonDev\": [\"pkg==ver\"], "
        "\"rust\": [\"crate@ver\"], "
        "\"go\": [\"module@ver\"], "
        "\"cpp\": [\"pkg\"]"
        "}, "
        "\"commands\": [str]"
        "}."
    )
    if persona_text.strip():
        system += (
            "\nApply this persona guidance for collaboration and coding behavior, "
            "unless it conflicts with safety or the explicit task:\n"
            f"{persona_text.strip()}"
        )
    user = f"Task:\n{task}\n\nContext Pack:\n{context_text}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _ordered_models(default_model: str, fallbacks: tuple[str, ...]) -> list[str]:
    """Return ordered model candidates without duplicates."""
    out: list[str] = []
    seen: set[str] = set()
    for model in [default_model, *fallbacks]:
        name = str(model).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def _run_openrouter_inference(
    *,
    project_root: Path,
    messages: list[dict[str, str]],
    model_candidates: list[str],
    max_tokens: int,
    max_retries: int,
    retry_backoff_sec: float,
    route_label: str,
) -> tuple[str, dict[str, int], float, str, list[dict[str, Any]], int]:
    """Run OpenRouter inference over ordered model candidates with retries."""
    _, _, openrouter_error_cls, load_dotenv = _get_elephant_exports()
    load_dotenv(project_root)
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise CLIError(
            "E_MODEL",
            "OPENROUTER_API_KEY is required for /code (set it in environment or .env).",
        )

    ordered = _ordered_models("", tuple(model_candidates))
    if not ordered:
        raise CLIError("E_MODEL", "No OpenRouter model candidates were provided.")

    client = _new_openrouter_client(api_key)
    result: Any | None = None
    selected_model = ordered[0]
    model_attempts: list[dict[str, Any]] = []
    retry_count = 0

    for model in ordered:
        attempts_allowed = 1 + max(0, int(max_retries))
        for attempt in range(1, attempts_allowed + 1):
            try:
                result = client.chat_completion(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.2,
                    timeout_sec=90,
                )
                selected_model = model
                model_attempts.append(
                    {
                        "model": model,
                        "attempt": attempt,
                        "success": True,
                        "error": "",
                        "retryable": False,
                        "fatal": False,
                        "route": route_label,
                    }
                )
                break
            except openrouter_error_cls as exc:
                msg = str(exc)
                retryable = _is_retryable_model_error(msg)
                fatal = _is_fatal_model_error(msg)
                can_retry = retryable and not fatal and attempt < attempts_allowed
                model_attempts.append(
                    {
                        "model": model,
                        "attempt": attempt,
                        "success": False,
                        "error": msg[:280],
                        "retryable": retryable,
                        "fatal": fatal,
                        "route": route_label,
                    }
                )
                if fatal:
                    raise CLIError("E_MODEL", msg) from exc
                if can_retry:
                    retry_count += 1
                    backoff_sec = retry_backoff_sec * (2 ** (attempt - 1))
                    if backoff_sec > 0:
                        time.sleep(min(backoff_sec, 8.0))
                    continue
                break
        if result is not None:
            break

    if result is None:
        if model_attempts:
            last = model_attempts[-1]
            last_err = str(last.get("error", "")).strip() or "unknown model error"
            attempted = len(model_attempts)
            raise CLIError(
                "E_MODEL",
                (
                    f"OpenRouter failed after {attempted} attempt(s) across "
                    f"{len(ordered)} model candidate(s): {last_err}"
                ),
            )
        raise CLIError("E_MODEL", "OpenRouter request failed before any attempt was recorded.")

    result_content = str(result.content or "")
    prompt_tokens = int(result.usage.get("prompt_tokens", 0))
    completion_tokens = int(result.usage.get("completion_tokens", 0))
    total_tokens = int(result.usage.get("total_tokens", prompt_tokens + completion_tokens))
    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
    estimated_cost = float(result.estimated_cost_usd)
    return result_content, usage, estimated_cost, selected_model, model_attempts, retry_count


def _is_retryable_model_error(message: str) -> bool:
    """Best-effort retryability classifier for OpenRouter/API errors."""
    low = str(message or "").lower()
    retryable_hints = (
        "http 408",
        "http 409",
        "http 425",
        "http 429",
        "http 500",
        "http 502",
        "http 503",
        "http 504",
        "network error",
        "timed out",
        "timeout",
        "connection reset",
        "temporarily unavailable",
    )
    return any(token in low for token in retryable_hints)


def _is_fatal_model_error(message: str) -> bool:
    """Detect failures that should stop retries/fallback immediately."""
    low = str(message or "").lower()
    fatal_hints = (
        "http 401",
        "http 403",
        "invalid api key",
        "openrouter_api_key is empty",
        "insufficient permissions",
    )
    return any(token in low for token in fatal_hints)


def _estimate_tokens_from_messages(messages: list[dict[str, str]]) -> int:
    """Rough token estimate from message content."""
    chars = 0
    for message in messages:
        chars += len(str(message.get("role", "")))
        chars += len(str(message.get("content", "")))
    return max(1, chars // 4)


def _extract_diff_file_paths(content: str, limit: int = 25) -> list[str]:
    """Extract touched file paths from unified diff-like output."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in content.splitlines():
        line = raw.strip()
        if line.startswith("+++ b/"):
            path = line[6:].strip()
        elif line.startswith("+++ "):
            path = line[4:].strip()
        else:
            continue
        if not path or path in {"/dev/null", "dev/null"}:
            continue
        norm = path.replace("\\", "/")
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
        if len(out) >= limit:
            break
    return out


def _extract_json_object(content: str) -> dict[str, Any] | None:
    """Extract first JSON object from model output."""
    text = str(content or "").strip()
    if not text:
        return None

    candidates: list[str] = [text]
    if "```" in text:
        parts = text.split("```")
        for block in parts[1::2]:
            body = block
            first_newline = body.find("\n")
            if first_newline != -1:
                header = body[:first_newline].strip().lower()
                payload = body[first_newline + 1 :].strip()
                if header in {"json", "javascript", "js", "ts", "typescript"}:
                    candidates.append(payload)
                else:
                    candidates.append(body.strip())
            else:
                candidates.append(body.strip())

    decoder = json.JSONDecoder()
    for cand in candidates:
        trimmed = cand.strip()
        if not trimmed:
            continue
        try:
            obj = json.loads(trimmed)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

        idx = 0
        while idx < len(trimmed):
            start = trimmed.find("{", idx)
            if start < 0:
                break
            try:
                obj, end = decoder.raw_decode(trimmed[start:])
            except json.JSONDecodeError:
                idx = start + 1
                continue
            if isinstance(obj, dict):
                return obj
            idx = start + max(1, end)
    return None


def _normalize_agent_plan(content: str) -> dict[str, Any]:
    """Normalize model output to an execution plan."""
    obj = _extract_json_object(content)
    if obj is None:
        return {
            "summary": "",
            "files": [],
            "dependencies": {
                "dependencies": {},
                "devDependencies": {},
                "python": [],
                "pythonDev": [],
                "rust": [],
                "go": [],
                "cpp": [],
            },
            "commands": [],
            "project": {},
            "raw_format": "unstructured",
        }

    files: list[dict[str, str]] = []
    raw_files = obj.get("files")
    if isinstance(raw_files, list):
        for item in raw_files:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path", "")).strip()
            if not path:
                continue
            content_value = str(item.get("content", ""))
            files.append({"path": path, "content": content_value})
    elif isinstance(raw_files, dict):
        for path, value in raw_files.items():
            p = str(path).strip()
            if not p:
                continue
            files.append({"path": p, "content": str(value)})

    raw_deps = obj.get("dependencies")
    deps: dict[str, str] = {}
    dev_deps: dict[str, str] = {}
    py_deps: list[str] = []
    py_dev_deps: list[str] = []
    rust_deps: list[str] = []
    go_deps: list[str] = []
    cpp_deps: list[str] = []
    if isinstance(raw_deps, dict):
        maybe_deps = raw_deps.get("dependencies", {})
        maybe_dev = raw_deps.get("devDependencies", {})
        if isinstance(maybe_deps, dict):
            deps = {str(k): str(v) for k, v in maybe_deps.items() if str(k).strip()}
        if isinstance(maybe_dev, dict):
            dev_deps = {str(k): str(v) for k, v in maybe_dev.items() if str(k).strip()}

        def _to_string_list(raw: Any) -> list[str]:
            if isinstance(raw, list):
                return [str(item).strip() for item in raw if str(item).strip()]
            if isinstance(raw, dict):
                out: list[str] = []
                for key, value in raw.items():
                    name = str(key).strip()
                    ver = str(value).strip()
                    if not name:
                        continue
                    if not ver or ver in {"*", "latest"}:
                        out.append(name)
                    else:
                        out.append(f"{name}=={ver}")
                return out
            if isinstance(raw, str) and raw.strip():
                return [raw.strip()]
            return []

        def _to_at_list(raw: Any) -> list[str]:
            if isinstance(raw, list):
                return [str(item).strip() for item in raw if str(item).strip()]
            if isinstance(raw, dict):
                out: list[str] = []
                for key, value in raw.items():
                    name = str(key).strip()
                    ver = str(value).strip()
                    if not name:
                        continue
                    if not ver or ver in {"*", "latest"}:
                        out.append(name)
                    else:
                        out.append(f"{name}@{ver}")
                return out
            if isinstance(raw, str) and raw.strip():
                return [raw.strip()]
            return []

        py_deps = _to_string_list(
            raw_deps.get("python")
            or raw_deps.get("pythonDependencies")
            or raw_deps.get("python_packages")
        )
        py_dev_deps = _to_string_list(
            raw_deps.get("pythonDev")
            or raw_deps.get("python_dev")
            or raw_deps.get("pythonDevDependencies")
            or raw_deps.get("python_dev_dependencies")
        )
        rust_deps = _to_at_list(raw_deps.get("rust") or raw_deps.get("cargo") or raw_deps.get("crates"))
        go_deps = _to_at_list(raw_deps.get("go") or raw_deps.get("golang") or raw_deps.get("goModules"))
        cpp_deps = _to_string_list(raw_deps.get("cpp") or raw_deps.get("c++") or raw_deps.get("cmake"))

        recognized_keys = {
            "dependencies",
            "devDependencies",
            "python",
            "pythonDependencies",
            "python_packages",
            "pythonDev",
            "python_dev",
            "pythonDevDependencies",
            "python_dev_dependencies",
            "rust",
            "cargo",
            "crates",
            "go",
            "golang",
            "goModules",
            "cpp",
            "c++",
            "cmake",
        }
        if (
            not deps
            and not dev_deps
            and not py_deps
            and not py_dev_deps
            and not rust_deps
            and not go_deps
            and not cpp_deps
            and not set(raw_deps.keys()).intersection(recognized_keys)
        ):
            deps = {str(k): str(v) for k, v in raw_deps.items() if str(k).strip()}

    commands: list[str] = []
    raw_commands = obj.get("commands")
    if isinstance(raw_commands, list):
        commands = [str(item).strip() for item in raw_commands if str(item).strip()]

    project = obj.get("project", {})
    if not isinstance(project, dict):
        project = {}

    return {
        "summary": str(obj.get("summary", "")).strip(),
        "files": files,
        "dependencies": {
            "dependencies": deps,
            "devDependencies": dev_deps,
            "python": py_deps,
            "pythonDev": py_dev_deps,
            "rust": rust_deps,
            "go": go_deps,
            "cpp": cpp_deps,
        },
        "commands": commands,
        "project": project,
        "raw_format": "json",
    }


def _plan_has_file_writes(plan: dict[str, Any]) -> bool:
    """Return True when structured plan includes file entries."""
    files = plan.get("files", [])
    return isinstance(files, list) and any(isinstance(item, dict) for item in files)


def _safe_target_path(project_root: Path, rel_path: str) -> tuple[Path, str]:
    """Resolve and validate output path is inside project root."""
    cleaned = rel_path.strip().replace("\\", "/")
    cleaned = cleaned[2:] if cleaned.startswith("./") else cleaned
    cleaned = cleaned.strip("/")
    if not cleaned:
        raise CLIError("E_STORAGE", "Agent file path is empty.")
    parts = Path(cleaned).parts
    if any(part in {"..", ""} for part in parts):
        raise CLIError("E_STORAGE", f"Unsafe file path from agent: {rel_path}")
    target = (project_root / cleaned).resolve()
    try:
        target.relative_to(project_root.resolve())
    except ValueError as exc:
        raise CLIError("E_STORAGE", f"Path escapes project root: {rel_path}") from exc
    return target, cleaned


def _read_json_file(path: Path) -> dict[str, Any] | None:
    """Read JSON file as object if present."""
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def _write_text_if_changed(path: Path, content: str) -> bool:
    """Write text file only when content changed."""
    current = None
    if path.exists() and path.is_file():
        try:
            current = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            current = None
    normalized = content.replace("\r\n", "\n")
    if current == normalized:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized, encoding="utf-8")
    return True


def _detect_package_manager(project_root: Path) -> str:
    """Detect node package manager from lockfiles."""
    if (project_root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (project_root / "yarn.lock").exists():
        return "yarn"
    if (project_root / "bun.lockb").exists() or (project_root / "bun.lock").exists():
        return "bun"
    return "npm"


def _run_command(project_root: Path, cmd: list[str], timeout_sec: int = 180) -> dict[str, Any]:
    """Run shell command and return compact result."""
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=timeout_sec,
        )
    except OSError as exc:
        return {"ok": False, "command": " ".join(cmd), "error": str(exc), "code": None}
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "command": " ".join(cmd), "error": f"timeout: {exc}", "code": None}

    out_tail = "\n".join((result.stdout or "").splitlines()[-20:])
    err_tail = "\n".join((result.stderr or "").splitlines()[-20:])
    return {
        "ok": result.returncode == 0,
        "command": " ".join(cmd),
        "code": int(result.returncode),
        "stdout_tail": out_tail,
        "stderr_tail": err_tail,
    }


def _canonical_language(name: str) -> str | None:
    """Normalize language aliases to canonical keys."""
    low = str(name or "").strip().lower()
    if low in {"typescript", "ts", "node", "nodejs", "javascript", "js"}:
        return "typescript"
    if low in {"python", "py"}:
        return "python"
    if low in {"rust", "rs"}:
        return "rust"
    if low in {"go", "golang"}:
        return "golang"
    if low in {"c++", "cpp", "cxx", "cc", "cmake"}:
        return "cpp"
    return None


def _infer_target_languages(task: str, plan: dict[str, Any]) -> list[str]:
    """Infer target languages from task text, plan metadata, files, and dependencies."""
    langs: set[str] = set()
    task_low = task.lower()
    task_hints = [
        ("typescript", "typescript"),
        ("ts project", "typescript"),
        ("node project", "typescript"),
        ("python", "python"),
        ("rust", "rust"),
        ("golang", "golang"),
        ("go module", "golang"),
        ("go project", "golang"),
        ("c++", "cpp"),
        ("cpp", "cpp"),
        ("cmake", "cpp"),
    ]
    for hint, lang in task_hints:
        if hint in task_low:
            langs.add(lang)

    project = plan.get("project", {})
    if isinstance(project, dict):
        raw_language = project.get("language")
        values: list[str] = []
        if isinstance(raw_language, list):
            values = [str(item) for item in raw_language]
        elif isinstance(raw_language, str):
            values = [part.strip() for part in raw_language.replace("/", ",").split(",")]
        for value in values:
            canon = _canonical_language(value)
            if canon:
                langs.add(canon)

    ext_map = {
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "typescript",
        ".jsx": "typescript",
        ".py": "python",
        ".rs": "rust",
        ".go": "golang",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".hh": "cpp",
    }
    plan_files = plan.get("files", [])
    if isinstance(plan_files, list):
        for item in plan_files:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path", "")).strip().lower()
            if not path:
                continue
            ext = Path(path).suffix.lower()
            lang = ext_map.get(ext)
            if lang:
                langs.add(lang)

    deps = plan.get("dependencies", {})
    if isinstance(deps, dict):
        if deps.get("dependencies") or deps.get("devDependencies"):
            langs.add("typescript")
        if deps.get("python") or deps.get("pythonDev"):
            langs.add("python")
        if deps.get("rust"):
            langs.add("rust")
        if deps.get("go"):
            langs.add("golang")
        if deps.get("cpp"):
            langs.add("cpp")

    return sorted(langs)


def _merge_dep_map(dst: dict[str, Any], src: dict[str, str]) -> bool:
    """Merge dependency map and report if changed."""
    changed = False
    for key, value in src.items():
        name = str(key).strip()
        ver = str(value).strip()
        if not name or not ver:
            continue
        if dst.get(name) != ver:
            dst[name] = ver
            changed = True
    return changed


def _merge_requirements_file(path: Path, deps: list[str]) -> bool:
    """Append missing dependency lines to requirements-like file."""
    cleaned = [str(item).strip() for item in deps if str(item).strip()]
    if not cleaned:
        return False
    existing_lines: list[str] = []
    existing_set: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            existing_lines.append(line.rstrip())
            if stripped and not stripped.startswith("#"):
                existing_set.add(stripped)

    changed = False
    for dep in cleaned:
        if dep not in existing_set:
            existing_lines.append(dep)
            existing_set.add(dep)
            changed = True
    if changed or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = "\n".join(existing_lines).strip() + "\n"
        path.write_text(payload, encoding="utf-8")
    return changed


def _ensure_typescript_bootstrap(
    project_root: Path,
    plan: dict[str, Any],
) -> tuple[list[str], bool]:
    """Ensure baseline TypeScript project files and dependencies."""
    files_written: list[str] = []
    package_changed = False

    package_path = project_root / "package.json"
    pkg = _read_json_file(package_path) or {}
    if not pkg:
        pkg = {
            "name": project_root.name.lower().replace(" ", "-"),
            "version": "0.1.0",
            "private": True,
            "scripts": {},
            "dependencies": {},
            "devDependencies": {},
        }
        package_changed = True

    scripts = pkg.get("scripts")
    if not isinstance(scripts, dict):
        scripts = {}
        pkg["scripts"] = scripts
        package_changed = True
    for key, value in {
        "build": "tsc -p tsconfig.json",
        "dev": "tsx src/main.ts",
        "start": "node dist/main.js",
    }.items():
        if key not in scripts:
            scripts[key] = value
            package_changed = True

    deps = pkg.get("dependencies")
    if not isinstance(deps, dict):
        deps = {}
        pkg["dependencies"] = deps
        package_changed = True
    dev_deps = pkg.get("devDependencies")
    if not isinstance(dev_deps, dict):
        dev_deps = {}
        pkg["devDependencies"] = dev_deps
        package_changed = True

    ts_defaults = {
        "typescript": "^5.6.3",
        "tsx": "^4.19.2",
        "@types/node": "^22.10.1",
    }
    if _merge_dep_map(dev_deps, ts_defaults):
        package_changed = True

    requested = plan.get("dependencies", {})
    if isinstance(requested, dict):
        req_deps = requested.get("dependencies", {})
        req_dev = requested.get("devDependencies", {})
        if isinstance(req_deps, dict) and _merge_dep_map(deps, req_deps):
            package_changed = True
        if isinstance(req_dev, dict) and _merge_dep_map(dev_deps, req_dev):
            package_changed = True

    if package_changed:
        package_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
        files_written.append("package.json")

    tsconfig_path = project_root / "tsconfig.json"
    if not tsconfig_path.exists():
        tsconfig = {
            "compilerOptions": {
                "target": "ES2022",
                "module": "NodeNext",
                "moduleResolution": "NodeNext",
                "strict": True,
                "outDir": "dist",
                "esModuleInterop": True,
                "forceConsistentCasingInFileNames": True,
                "skipLibCheck": True,
            },
            "include": ["src/**/*.ts"],
        }
        tsconfig_path.write_text(json.dumps(tsconfig, indent=2) + "\n", encoding="utf-8")
        files_written.append("tsconfig.json")

    return files_written, package_changed


def _ensure_python_bootstrap(project_root: Path, plan: dict[str, Any]) -> tuple[list[str], bool]:
    """Ensure baseline Python project files and dependency manifests."""
    files_written: list[str] = []
    dep_changed = False

    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        pyproject = "\n".join(
            [
                "[project]",
                f'name = "{project_root.name.lower().replace(" ", "-")}"',
                'version = "0.1.0"',
                "requires-python = \">=3.12\"",
                "",
                "[tool.uv]",
                "managed = true",
                "",
            ]
        )
        pyproject_path.write_text(pyproject, encoding="utf-8")
        files_written.append("pyproject.toml")

    deps = plan.get("dependencies", {})
    py_deps: list[str] = []
    py_dev: list[str] = []
    if isinstance(deps, dict):
        raw_py = deps.get("python", [])
        raw_py_dev = deps.get("pythonDev", [])
        if isinstance(raw_py, list):
            py_deps = [str(item).strip() for item in raw_py if str(item).strip()]
        if isinstance(raw_py_dev, list):
            py_dev = [str(item).strip() for item in raw_py_dev if str(item).strip()]

    req_path = project_root / "requirements.txt"
    req_dev_path = project_root / "requirements-dev.txt"
    req_changed = _merge_requirements_file(req_path, py_deps)
    req_dev_changed = _merge_requirements_file(req_dev_path, py_dev)
    if req_changed:
        files_written.append("requirements.txt")
    if req_dev_changed:
        files_written.append("requirements-dev.txt")
    dep_changed = req_changed or req_dev_changed
    return files_written, dep_changed


def _ensure_rust_bootstrap(project_root: Path, plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Ensure baseline Rust project files and return dependency specs."""
    files_written: list[str] = []
    deps = plan.get("dependencies", {})
    rust_deps: list[str] = []
    if isinstance(deps, dict) and isinstance(deps.get("rust"), list):
        rust_deps = [str(item).strip() for item in deps.get("rust", []) if str(item).strip()]

    cargo_path = project_root / "Cargo.toml"
    if not cargo_path.exists():
        cargo_text = "\n".join(
            [
                "[package]",
                f'name = "{project_root.name.lower().replace(" ", "-")}"',
                'version = "0.1.0"',
                'edition = "2021"',
                "",
                "[dependencies]",
                "",
            ]
        )
        cargo_path.write_text(cargo_text, encoding="utf-8")
        files_written.append("Cargo.toml")

    main_rs = project_root / "src" / "main.rs"
    if not main_rs.exists():
        main_rs.parent.mkdir(parents=True, exist_ok=True)
        main_rs.write_text("fn main() {\n    println!(\"hello world\");\n}\n", encoding="utf-8")
        files_written.append("src/main.rs")

    return files_written, rust_deps


def _ensure_go_bootstrap(project_root: Path, plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Ensure baseline Go project files and return module specs."""
    files_written: list[str] = []
    deps = plan.get("dependencies", {})
    go_deps: list[str] = []
    if isinstance(deps, dict) and isinstance(deps.get("go"), list):
        go_deps = [str(item).strip() for item in deps.get("go", []) if str(item).strip()]

    go_mod = project_root / "go.mod"
    if not go_mod.exists():
        module_name = project_root.name.lower().replace(" ", "-")
        go_mod.write_text(f"module {module_name}\n\ngo 1.22\n", encoding="utf-8")
        files_written.append("go.mod")

    main_go = project_root / "main.go"
    if not main_go.exists():
        main_go.write_text(
            "\n".join(
                [
                    "package main",
                    "",
                    "import \"fmt\"",
                    "",
                    "func main() {",
                    "    fmt.Println(\"hello world\")",
                    "}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        files_written.append("main.go")
    return files_written, go_deps


def _ensure_cpp_bootstrap(project_root: Path, plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Ensure baseline C++ project files and return declared C++ deps."""
    files_written: list[str] = []
    deps = plan.get("dependencies", {})
    cpp_deps: list[str] = []
    if isinstance(deps, dict) and isinstance(deps.get("cpp"), list):
        cpp_deps = [str(item).strip() for item in deps.get("cpp", []) if str(item).strip()]

    cmake_path = project_root / "CMakeLists.txt"
    if not cmake_path.exists():
        extra = ""
        if cpp_deps:
            extra = "# Declared dependencies: " + ", ".join(cpp_deps) + "\n"
        cmake_text = "\n".join(
            [
                "cmake_minimum_required(VERSION 3.16)",
                f"project({project_root.name} LANGUAGES CXX)",
                "set(CMAKE_CXX_STANDARD 17)",
                "set(CMAKE_CXX_STANDARD_REQUIRED ON)",
                extra.strip(),
                "add_executable(app src/main.cpp)",
                "",
            ]
        )
        cmake_path.write_text(cmake_text, encoding="utf-8")
        files_written.append("CMakeLists.txt")

    main_cpp = project_root / "src" / "main.cpp"
    if not main_cpp.exists():
        main_cpp.parent.mkdir(parents=True, exist_ok=True)
        main_cpp.write_text(
            "\n".join(
                [
                    "#include <iostream>",
                    "",
                    "int main() {",
                    '    std::cout << "hello world" << std::endl;',
                    "    return 0;",
                    "}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        files_written.append("src/main.cpp")
    return files_written, cpp_deps


def _apply_agent_plan(
    *,
    project_root: Path,
    task: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """Apply parsed agent plan to disk and install dependencies when needed."""
    files_written: list[str] = []
    install_results: list[dict[str, Any]] = []
    plan_files = plan.get("files", [])
    if isinstance(plan_files, list):
        for item in plan_files:
            if not isinstance(item, dict):
                continue
            rel_path = str(item.get("path", "")).strip()
            content = str(item.get("content", ""))
            if not rel_path:
                continue
            target, clean_rel = _safe_target_path(project_root, rel_path)
            if _write_text_if_changed(target, content):
                files_written.append(clean_rel)
    languages = _infer_target_languages(task, plan)

    bootstrapped_files: list[str] = []
    if "typescript" in languages:
        ts_written, ts_package_changed = _ensure_typescript_bootstrap(project_root, plan)
        for rel in ts_written:
            if rel not in files_written:
                bootstrapped_files.append(rel)
        if ts_package_changed or "package.json" in files_written:
            package_manager = _detect_package_manager(project_root)
            install_cmd = {
                "npm": ["npm", "install"],
                "pnpm": ["pnpm", "install"],
                "yarn": ["yarn", "install"],
                "bun": ["bun", "install"],
            }.get(package_manager, ["npm", "install"])
            install_results.append(_run_command(project_root, install_cmd))

    if "python" in languages:
        py_written, py_deps_changed = _ensure_python_bootstrap(project_root, plan)
        for rel in py_written:
            if rel not in files_written and rel not in bootstrapped_files:
                bootstrapped_files.append(rel)
        if py_deps_changed:
            install_results.append(
                _run_command(
                    project_root,
                    ["uv", "pip", "install", "--python", "3.12", "-r", "requirements.txt"],
                )
            )
            if (project_root / "requirements-dev.txt").exists():
                install_results.append(
                    _run_command(
                        project_root,
                        ["uv", "pip", "install", "--python", "3.12", "-r", "requirements-dev.txt"],
                    )
                )

    if "rust" in languages:
        rust_written, rust_deps = _ensure_rust_bootstrap(project_root, plan)
        for rel in rust_written:
            if rel not in files_written and rel not in bootstrapped_files:
                bootstrapped_files.append(rel)
        for dep in rust_deps:
            install_results.append(_run_command(project_root, ["cargo", "add", dep]))

    if "golang" in languages:
        go_written, go_deps = _ensure_go_bootstrap(project_root, plan)
        for rel in go_written:
            if rel not in files_written and rel not in bootstrapped_files:
                bootstrapped_files.append(rel)
        for dep in go_deps:
            install_results.append(_run_command(project_root, ["go", "get", dep]))
        if go_deps:
            install_results.append(_run_command(project_root, ["go", "mod", "tidy"]))

    if "cpp" in languages:
        cpp_written, _cpp_deps = _ensure_cpp_bootstrap(project_root, plan)
        for rel in cpp_written:
            if rel not in files_written and rel not in bootstrapped_files:
                bootstrapped_files.append(rel)
        if (project_root / "CMakeLists.txt").exists():
            install_results.append(_run_command(project_root, ["cmake", "-S", ".", "-B", "build"]))

    return {
        "files_written": sorted(set(files_written + bootstrapped_files)),
        "files_written_count": len(set(files_written + bootstrapped_files)),
        "bootstrap_languages": languages,
        "dependencies_install": install_results,
        "applied_from_structured_plan": plan.get("raw_format") == "json",
    }


def _get_git_diff_text(project_root: Path, max_lines: int) -> str:
    """Return compact git diff text (staged + unstaged)."""
    chunks: list[str] = []
    for label, extra in (("staged", ["--cached"]), ("unstaged", [])):
        try:
            result = subprocess.run(
                ["git", "-C", str(project_root), "diff", "--no-color", *extra, "--", "."],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            return f"(git unavailable: {exc})"
        if result.returncode != 0:
            continue
        text = result.stdout.strip()
        if text:
            chunks.append(f"# {label}\n{text}")
    if not chunks:
        return "(no local diff)"
    lines: list[str] = []
    for item in chunks:
        lines.extend(item.splitlines())
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... (truncated to {max_lines} lines)"]
    return "\n".join(lines)


def _render_file_chunk(path: Path, rel: str, max_lines: int, max_chars: int) -> tuple[str, bool]:
    """Render one file snippet with line numbers."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"### {rel}\n(read failed: {exc})", False

    truncated = len(lines) > max_lines
    view = lines[:max_lines]
    numbered = "\n".join(f"{idx + 1:4d}: {line}" for idx, line in enumerate(view))
    if len(numbered) > max_chars:
        numbered = numbered[:max_chars]
        truncated = True
    suffix = "\n... (truncated)" if truncated else ""
    return f"### {rel}\n```python\n{numbered}\n```\n{suffix}".strip(), truncated


def _collect_code_chunks(
    project_root: Path,
    candidate_files: list[str],
    max_files: int,
    max_lines_per_file: int,
    max_total_chars: int,
) -> tuple[str, dict[str, Any]]:
    """Collect code chunks from selected files with hard limits."""
    picked: list[str] = []
    blocks: list[str] = []
    truncated_any = False
    total_chars = 0
    for rel in candidate_files[: max(1, max_files)]:
        if total_chars >= max_total_chars:
            break
        path = (project_root / rel).resolve()
        if not path.exists() or not path.is_file():
            continue
        block, truncated = _render_file_chunk(path, rel, max_lines=max_lines_per_file, max_chars=4000)
        if not block:
            continue
        if total_chars + len(block) > max_total_chars:
            remaining = max_total_chars - total_chars
            if remaining <= 128:
                break
            block = block[:remaining] + "\n... (truncated total)"
            truncated = True
        blocks.append(block)
        picked.append(rel)
        total_chars += len(block)
        truncated_any = truncated_any or truncated

    if not blocks:
        return "(no code chunks selected)", {"files": [], "count": 0, "truncated": False}
    return "\n\n".join(blocks), {"files": picked, "count": len(picked), "truncated": truncated_any}


def _load_vsa_binary_ops() -> tuple[Any | None, str | None]:
    """Load BinaryOps from grilly.experimental.vsa with fallback import path."""
    try:
        from grilly.experimental.vsa import BinaryOps  # type: ignore[import-not-found]

        return BinaryOps, None
    except Exception:
        try:
            from experimental.vsa import BinaryOps  # type: ignore[import-not-found]

            return BinaryOps, None
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"


def _vector_fingerprint(vec: Any, bits: int = 64) -> str:
    """Compact fingerprint for a bipolar vector."""
    n = max(8, bits)
    raw_bits = "".join("1" if float(vec[i]) > 0 else "0" for i in range(min(n, len(vec))))
    if len(raw_bits) % 4:
        raw_bits += "0" * (4 - (len(raw_bits) % 4))
    hex_chars: list[str] = []
    for i in range(0, len(raw_bits), 4):
        chunk = raw_bits[i : i + 4]
        hex_chars.append(format(int(chunk, 2), "x"))
    return "".join(hex_chars)


def _vsa_rank_candidate_files(
    task: str,
    candidate_files: list[str],
    *,
    dim: int = 1024,
) -> tuple[list[str], dict[str, Any]]:
    """Rank candidate files by VSA similarity to task signature."""
    if not candidate_files:
        return [], {"enabled": False, "error": "no candidates"}

    binary_ops, err = _load_vsa_binary_ops()
    if binary_ops is None:
        return candidate_files, {"enabled": False, "error": f"vsa unavailable: {err}"}

    task_vec = binary_ops.hash_to_bipolar(f"task:{task[:2048]}", dim)
    scored: list[tuple[float, int, str]] = []
    for idx, file_path in enumerate(candidate_files):
        file_vec = binary_ops.hash_to_bipolar(f"file:{file_path}", dim)
        sim = float(binary_ops.similarity(task_vec, file_vec))
        scored.append((sim, idx, file_path))
    scored.sort(key=lambda x: (-x[0], x[1]))
    ranked = [item[2] for item in scored]
    top = [{"file_path": item[2], "similarity": round(item[0], 4)} for item in scored[:10]]
    return ranked, {
        "enabled": True,
        "error": None,
        "dim": dim,
        "top_similarities": top,
    }


def _build_vsa_structure(
    *,
    task: str,
    impacted_text: str,
    ast_graph_text: str,
    git_diff_text: str,
    chunks_text: str,
    traces_text: str,
    dim: int = 1024,
) -> dict[str, Any]:
    """Build VSA structural summary across context modalities."""
    binary_ops, err = _load_vsa_binary_ops()
    if binary_ops is None:
        return {"enabled": False, "error": f"vsa unavailable: {err}"}

    task_vec = binary_ops.hash_to_bipolar(f"task:{task[:2048]}", dim)
    sections = {
        "impacted_files": impacted_text[:4096],
        "ast_graph": ast_graph_text[:4096],
        "git_diff": git_diff_text[:4096],
        "code_chunks": chunks_text[:4096],
        "runtime_traces": traces_text[:4096],
    }

    vectors: list[Any] = []
    similarities: dict[str, float] = {}
    section_fingerprints: dict[str, str] = {}
    for key, text in sections.items():
        vec = binary_ops.hash_to_bipolar(f"{key}:{text}", dim)
        vectors.append(vec)
        similarities[key] = round(float(binary_ops.similarity(task_vec, vec)), 4)
        section_fingerprints[key] = _vector_fingerprint(vec, bits=48)

    bundle = binary_ops.bundle(vectors)
    bundle_similarity = round(float(binary_ops.similarity(task_vec, bundle)), 4)
    return {
        "enabled": True,
        "error": None,
        "dim": dim,
        "task_fingerprint": _vector_fingerprint(task_vec),
        "bundle_fingerprint": _vector_fingerprint(bundle),
        "section_fingerprints": section_fingerprints,
        "similarity_to_task": similarities,
        "bundle_similarity_to_task": bundle_similarity,
    }


def _collect_ast_graph_features(
    index: Any,
    impacted_files: list[str],
    max_symbols: int,
    max_edges: int,
) -> tuple[str, dict[str, Any]]:
    """Collect AST/graph features around impacted files."""
    file_set = set(impacted_files)
    symbols = []
    for item in index.store.list_symbols():  # type: ignore[attr-defined]
        if item["file_path"] in file_set:
            symbols.append(item)
    symbols.sort(key=lambda x: (x["file_path"], int(x["lineno"]), x["qualname"]))
    symbols = symbols[:max_symbols]

    edges = []
    for edge in index.store.list_edges():  # type: ignore[attr-defined]
        if edge["src_file"] in file_set or edge["dst_file"] in file_set:
            edges.append(edge)
    edges.sort(key=lambda x: (x["src_file"], x["dst_file"], x["edge_type"]))
    edges = edges[:max_edges]

    symbol_lines = []
    for sym in symbols:
        signature = str(sym.get("signature") or "").strip()
        sig = f" | {signature}" if signature else ""
        line = (
            f"- {sym['file_path']}:{sym['lineno']} [{sym['kind']}] {sym['qualname']}{sig}"
        )
        if len(line) > 220:
            line = f"{line[:220]}..."
        symbol_lines.append(line)
    edge_lines = [
        f"- {edge['src_file']} -> {edge['dst_file']} ({edge['edge_type']}, w={float(edge['weight']):.2f})"
        for edge in edges
    ]
    edge_lines = [f"{line[:220]}..." if len(line) > 220 else line for line in edge_lines]
    text = (
        "Symbols:\n"
        + ("\n".join(symbol_lines) if symbol_lines else "- (none)")
        + "\n\nGraph edges:\n"
        + ("\n".join(edge_lines) if edge_lines else "- (none)")
    )
    manifest = {
        "symbol_count": len(symbols),
        "edge_count": len(edges),
        "files_considered": sorted(file_set),
    }
    return text, manifest


def _collect_runtime_traces(project_root: Path, max_runs: int) -> tuple[str, dict[str, Any]]:
    """Collect recent run-level test/runtime traces."""
    if max_runs <= 0:
        return "(runtime traces disabled)", {"count": 0, "commands": [], "disabled": True}

    runs_dir = project_root / ".elephant-coder" / "runs"
    if not runs_dir.exists():
        return "(no run records)", {"count": 0, "commands": []}

    files = sorted(
        runs_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[: max(1, max_runs)]

    lines: list[str] = []
    commands: set[str] = set()
    for rec in files:
        try:
            payload = json.loads(rec.read_text(encoding="utf-8"))
        except Exception:
            continue
        cmd = str(payload.get("command", ""))
        ok = bool(payload.get("ok", False))
        metrics = payload.get("metrics", {}) or {}
        latency = int(metrics.get("latency_ms", 0) or 0)
        total_tokens = int(metrics.get("total_tokens", 0) or 0)
        cost = float(metrics.get("estimated_cost_usd", 0.0) or 0.0)
        errors = payload.get("errors", []) or []
        error_codes = ",".join(str(e.get("code", "")) for e in errors if isinstance(e, dict))
        line = (
            f"- run={payload.get('run_id', '')} cmd={cmd} ok={ok} "
            f"latency_ms={latency} tokens={total_tokens} cost_usd={cost:.6f}"
        )
        if error_codes:
            line += f" errors={error_codes}"

        if cmd == "/test":
            data = payload.get("data", {}) or {}
            selected = len(data.get("tests_selected", []) or [])
            results = data.get("results", {}) or {}
            line += f" tests_selected={selected} test_status={results.get('status', '')}"
        lines.append(line)
        if cmd:
            commands.add(cmd)

    if not lines:
        return "(no parseable run records)", {"count": 0, "commands": []}
    return "\n".join(lines), {"count": len(lines), "commands": sorted(commands)}


def _build_context_pack(
    *,
    project_root: Path,
    index: Any,
    impact: dict[str, Any],
    index_stats: dict[str, Any],
    changed_files: list[str],
    task: str,
    profile: dict[str, int],
) -> tuple[str, dict[str, Any]]:
    """Build multimodal context pack for /code."""
    impacted_files = [item["file_path"] for item in impact.get("impacted", [])]
    top_impacted = impacted_files[: max(1, profile["max_impacted_files"])]
    if not top_impacted:
        indexed = sorted(index.store.get_indexed_file_meta().keys())  # type: ignore[attr-defined]
        top_impacted = indexed[: max(1, profile["max_impacted_files"])]
    candidate_files = top_impacted if top_impacted else changed_files
    ranked_files, vsa_ranking = _vsa_rank_candidate_files(task, candidate_files, dim=1024)
    if vsa_ranking.get("enabled"):
        candidate_files = ranked_files

    chunks_text, chunk_manifest = _collect_code_chunks(
        project_root=project_root,
        candidate_files=candidate_files,
        max_files=profile["chunk_files"],
        max_lines_per_file=profile["chunk_lines"],
        max_total_chars=profile["chunk_chars_total"],
    )
    ast_graph_text, ast_graph_manifest = _collect_ast_graph_features(
        index=index,
        impacted_files=top_impacted,
        max_symbols=profile["max_symbols"],
        max_edges=profile["max_edges"],
    )
    git_diff_text = _get_git_diff_text(project_root, max_lines=profile["diff_lines"])
    traces_text, traces_manifest = _collect_runtime_traces(
        project_root,
        max_runs=profile["trace_runs"],
    )
    vsa_structure = _build_vsa_structure(
        task=task,
        impacted_text="\n".join(top_impacted),
        ast_graph_text=ast_graph_text,
        git_diff_text=git_diff_text,
        chunks_text=chunks_text,
        traces_text=traces_text,
        dim=1024,
    )

    impacted_lines = [
        (
            f"- {item['file_path']} distance={item['distance']} "
            f"kind={item['impact_kind']} source={item['impact_source']} "
            f"confidence={item['confidence']}"
        )
        for item in impact.get("impacted", [])[: max(1, profile["max_impacted_files"])]
    ]
    impacted_text = "\n".join(impacted_lines) if impacted_lines else "- (none)"
    if vsa_structure.get("enabled"):
        similarity = vsa_structure.get("similarity_to_task", {})
        vsa_summary = (
            f"- bundle_similarity_to_task={vsa_structure.get('bundle_similarity_to_task', 0.0)}\n"
            f"- top_modalities={json.dumps(similarity)}\n"
            f"- task_fingerprint={vsa_structure.get('task_fingerprint', '')}\n"
            f"- bundle_fingerprint={vsa_structure.get('bundle_fingerprint', '')}\n"
        )
    else:
        vsa_summary = f"- disabled: {vsa_structure.get('error', 'unknown')}\n"

    context = (
        "## Impacted Files\n"
        f"{impacted_text}\n\n"
        "## VSA Structure\n"
        f"{vsa_summary}\n"
        "## AST/Graph Features\n"
        f"{ast_graph_text}\n\n"
        "## Git Diff\n"
        f"```diff\n{git_diff_text}\n```\n\n"
        "## Code Chunks\n"
        f"{chunks_text}\n\n"
        "## Test and Runtime Traces\n"
        f"{traces_text}\n\n"
        "## Context Notes\n"
        f"- index_files_scanned={index_stats.get('files_scanned', 0)}\n"
        f"- index_edges_total={index_stats.get('edges_total', 0)}\n"
        f"- world_model_enabled={impact.get('world_model', {}).get('enabled', False)}\n"
        f"- task={task}\n"
    )

    manifest = {
        "modalities": {
            "vsa_structure": vsa_structure,
            "code_chunks": chunk_manifest,
            "ast_graph_features": ast_graph_manifest,
            "git_diff": {
                "line_count": len(git_diff_text.splitlines()),
                "is_empty": git_diff_text.startswith("(no local diff)"),
            },
            "test_runtime_traces": traces_manifest,
        },
        "impacted_files_used": top_impacted,
        "vsa_file_ranking": vsa_ranking,
    }
    return context, manifest


def _command_plan(args: argparse.Namespace, project_root: Path) -> dict[str, Any]:
    """Plan command with index + impact analysis."""
    task = args.task or "No task provided."
    requested_persona = str(getattr(args, "persona", "") or "").strip() or None
    active_persona, persona_text, persona_meta, persona_warnings = _load_persona_guidance(
        project_root,
        requested_persona,
        max_chars=2200,
    )
    persona_adjust = _persona_plan_adjustments(persona_text)

    index = _new_index_service(project_root)
    try:
        index_stats = index.refresh_index()
        _, changed, _ = _git_status(project_root)
        changed_py = _changed_python_files(project_root, changed)
        impact = index.impact_for_files(changed_py)
    finally:
        index.close()

    impacted_files = [item["file_path"] for item in impact["impacted"][:20]]
    cot_steps = _dedupe_lines(
        [
            "Interpret task intent and active persona constraints.",
            "Refresh index and compute changed-file impact graph.",
            "Prioritize impacted files by risk and dependency order.",
            "Define execution sequence and validation checkpoints.",
            "Document assumptions and residual risks before implementation.",
        ]
    )
    assumptions: list[str] = []
    if not changed_py:
        assumptions.append("No changed Python files detected from git status.")
    assumptions.append("Agent dispatch and context compression are still scaffold implementations.")
    assumptions.extend(persona_adjust["assumptions"])
    assumptions = _dedupe_lines(assumptions)

    plan_steps = [
        "Refresh incremental Python index and dependency graph.",
        "Compute changed-file impact set (direct and transitive).",
        "Plan implementation sequence against highest-impact files first.",
    ]
    plan_steps.extend(persona_adjust["plan_steps"])
    plan_steps = _dedupe_lines(plan_steps)

    risks = [
        "Dynamic imports and runtime reflection are not fully captured by static analysis.",
        "Cross-language dependencies are out of scope in v1 (Python-only index).",
    ]
    risks.extend(persona_adjust["risks"])
    risks = _dedupe_lines(risks)

    plan_md = _build_plan_markdown(
        task=task,
        active_persona=active_persona,
        cot_steps=cot_steps,
        plan_steps=plan_steps,
        assumptions=assumptions,
        risks=risks,
        impacted_files=impacted_files,
        persona_signals=persona_adjust["signals"],
        index_stats=index_stats,
        impact_report=impact,
    )
    plan_path = project_root / "PLAN.md"
    plan_written = _write_text_if_changed(plan_path, plan_md)

    return {
        "cot_steps": cot_steps,
        "plan_steps": plan_steps,
        "impacted_files": impacted_files,
        "assumptions": assumptions,
        "risks": risks,
        "plan_file": plan_path.as_posix(),
        "plan_file_written": plan_written,
        "active_persona": active_persona,
        "persona_manifest": persona_meta,
        "persona_signals": persona_adjust["signals"],
        "index_stats": index_stats,
        "impact_report": impact,
        "task": task,
        "_warnings": persona_warnings,
    }


def _command_code(args: argparse.Namespace, project_root: Path) -> dict[str, Any]:
    """Run code command through one OpenRouter worker, with budget checks."""
    task = args.task or "No task provided."
    mode = str(getattr(args, "mode", "elephant") or "elephant").strip().lower()
    router_mode = str(getattr(args, "router", "auto") or "auto").strip().lower()
    requested_specialist = str(getattr(args, "specialist", "") or "").strip() or None
    benchmark_parity = bool(getattr(args, "benchmark_parity", False))
    if mode not in {"elephant", "baseline"}:
        raise CLIError("E_CONFIG", f"Unsupported code mode: {mode}")
    runtime: RuntimeConfig = args._runtime  # type: ignore[attr-defined]
    dry_run = bool(getattr(args, "dry_run", False))
    no_apply = bool(getattr(args, "no_apply", False))
    session_id = str(getattr(args, "_session_id", "") or "")
    requested_persona = str(getattr(args, "persona", "") or "").strip() or None
    session_context_text, session_context_meta = _load_session_context(
        project_root,
        session_id,
        max_events=10,
        max_chars=2200,
    )
    active_persona, persona_text, persona_meta, persona_warnings = _load_persona_guidance(
        project_root,
        requested_persona,
        max_chars=2600,
    )

    index = _new_index_service(project_root)
    try:
        index_stats = index.refresh_index()
        _, changed, _ = _git_status(project_root)
        changed_py = _changed_python_files(project_root, changed)
        impact = index.impact_for_files(changed_py)
        elephant_profiles = [
            {
                "name": "full",
                "max_impacted_files": 20,
                "chunk_files": 8,
                "chunk_lines": 120,
                "chunk_chars_total": 22000,
                "max_symbols": 120,
                "max_edges": 120,
                "diff_lines": 300,
                "trace_runs": 12,
            },
            {
                "name": "balanced",
                "max_impacted_files": 16,
                "chunk_files": 6,
                "chunk_lines": 90,
                "chunk_chars_total": 16000,
                "max_symbols": 90,
                "max_edges": 90,
                "diff_lines": 220,
                "trace_runs": 10,
            },
            {
                "name": "tight",
                "max_impacted_files": 12,
                "chunk_files": 5,
                "chunk_lines": 60,
                "chunk_chars_total": 11000,
                "max_symbols": 60,
                "max_edges": 60,
                "diff_lines": 160,
                "trace_runs": 8,
            },
            {
                "name": "minimal",
                "max_impacted_files": 8,
                "chunk_files": 3,
                "chunk_lines": 40,
                "chunk_chars_total": 7000,
                "max_symbols": 40,
                "max_edges": 40,
                "diff_lines": 100,
                "trace_runs": 6,
            },
            {
                "name": "micro",
                "max_impacted_files": 4,
                "chunk_files": 2,
                "chunk_lines": 20,
                "chunk_chars_total": 2200,
                "max_symbols": 20,
                "max_edges": 20,
                "diff_lines": 40,
                "trace_runs": 4,
            },
            {
                "name": "nano",
                "max_impacted_files": 2,
                "chunk_files": 1,
                "chunk_lines": 10,
                "chunk_chars_total": 700,
                "max_symbols": 8,
                "max_edges": 8,
                "diff_lines": 20,
                "trace_runs": 2,
            },
        ]
        baseline_profiles = [
            {
                "name": "baseline_large",
                "max_impacted_files": 40,
                "chunk_files": 12,
                "chunk_lines": 140,
                "chunk_chars_total": 32000,
                "max_symbols": 180,
                "max_edges": 180,
                "diff_lines": 500,
                "trace_runs": 0,
            },
            {
                "name": "baseline_medium",
                "max_impacted_files": 30,
                "chunk_files": 10,
                "chunk_lines": 110,
                "chunk_chars_total": 24000,
                "max_symbols": 140,
                "max_edges": 140,
                "diff_lines": 360,
                "trace_runs": 0,
            },
            {
                "name": "baseline_small",
                "max_impacted_files": 24,
                "chunk_files": 8,
                "chunk_lines": 85,
                "chunk_chars_total": 17000,
                "max_symbols": 100,
                "max_edges": 100,
                "diff_lines": 260,
                "trace_runs": 0,
            },
            {
                "name": "baseline_micro",
                "max_impacted_files": 12,
                "chunk_files": 4,
                "chunk_lines": 60,
                "chunk_chars_total": 9000,
                "max_symbols": 60,
                "max_edges": 60,
                "diff_lines": 140,
                "trace_runs": 0,
            }
        ]
        profiles = elephant_profiles
        if mode == "baseline":
            profiles = baseline_profiles
        if benchmark_parity:
            profiles = baseline_profiles
        context_text = ""
        context_manifest: dict[str, Any] = {}
        profile_name = "minimal"
        estimated_input_tokens = runtime.max_input_tokens + 1
        messages: list[dict[str, str]] = []
        profile_results: list[tuple[str, str, dict[str, Any], list[dict[str, str]], int]] = []
        for profile in profiles:
            pack_text, pack_manifest = _build_context_pack(
                project_root=project_root,
                index=index,
                impact=impact,
                index_stats=index_stats,
                changed_files=changed_py,
                task=task,
                profile=profile,
            )
            if mode == "elephant" and session_context_text and not benchmark_parity:
                combined_context = pack_text + "\n\n## Session Context\n" + session_context_text
            else:
                combined_context = pack_text
            candidate_messages = _build_code_messages(
                task=task,
                context_text=combined_context,
                persona_text=persona_text,
            )
            estimated = _estimate_tokens_from_messages(candidate_messages)
            profile_results.append(
                (
                    str(profile["name"]),
                    combined_context,
                    pack_manifest,
                    candidate_messages,
                    estimated,
                )
            )

        soft_target_tokens = max(
            256,
            min(runtime.max_input_tokens, int(runtime.max_input_tokens * 0.6), 3500),
        )
        if mode == "baseline" or benchmark_parity:
            soft_target_tokens = runtime.max_input_tokens
        selected: tuple[str, str, dict[str, Any], list[dict[str, str]], int] | None = None
        for item in profile_results:
            if item[4] <= soft_target_tokens:
                selected = item
                break
        if selected is None:
            for item in profile_results:
                if item[4] <= runtime.max_input_tokens:
                    selected = item
                    break
        if selected is None and profile_results:
            selected = profile_results[-1]

        if selected is not None:
            profile_name, context_text, context_manifest, messages, estimated_input_tokens = selected
            if mode == "elephant" and not benchmark_parity:
                context_manifest["session_context"] = session_context_meta
            context_manifest["persona"] = persona_meta
            context_manifest["mode"] = mode
            context_manifest["benchmark_parity"] = benchmark_parity
    finally:
        index.close()

    if estimated_input_tokens > runtime.max_input_tokens:
        raise CLIError(
            "E_BUDGET",
            (
                f"Estimated prompt tokens {estimated_input_tokens} exceed "
                f"max-input-tokens {runtime.max_input_tokens}."
            ),
        )

    routing, route_warnings = _route_for_code(
        project_root=project_root,
        router_mode=router_mode,
        task=task,
        requested_specialist=requested_specialist,
    )

    if dry_run:
        return {
            "changes": [],
            "files_touched": context_manifest.get("impacted_files_used", [])[:10],
            "agent_reports": [
                {
                    "agent_id": "worker_1",
                    "model": runtime.default_model,
                    "status": "dry_run",
                    "summary": "Dispatch skipped (--dry-run).",
                    "estimated_input_tokens": estimated_input_tokens,
                }
            ],
            "verification_summary": "No checks executed in dry-run mode.",
            "task": task,
            "dry_run": True,
            "no_apply": no_apply,
            "mode": mode,
            "benchmark_parity": benchmark_parity,
            "router_mode": router_mode,
            "routing": routing,
            "project_root": str(project_root),
            "index_stats": index_stats,
            "impact_report": impact,
            "context_profile": profile_name,
            "context_manifest": context_manifest,
            "_warnings": route_warnings,
        }

    result_content = ""
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    estimated_cost = 0.0
    selected_model = runtime.default_model
    model_attempts: list[dict[str, Any]] = []
    retry_count = 0
    model_candidates: list[str] = []

    if routing["route"] == "local":
        specialist, _ = _select_local_specialist(project_root, task, requested_specialist)
        if specialist is None:
            raise CLIError("E_MODEL", "Local route selected but no specialist was resolved.")
        specialist_backend = str(specialist.get("backend", "llama_cpp_cli")).strip().lower()
        if specialist_backend == "llama_cpp_cli":
            result_content, usage, local_cost = _run_local_specialist_inference(
                project_root=project_root,
                spec=specialist,
                messages=messages,
                max_tokens=runtime.max_output_tokens,
                timeout_sec=120,
            )
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
            total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))
            estimated_cost = float(local_cost)
            selected_model = str(specialist.get("id", "local-specialist"))
            model_candidates = [selected_model]
            model_attempts = [
                {
                    "model": selected_model,
                    "attempt": 1,
                    "success": True,
                    "error": "",
                    "retryable": False,
                    "fatal": False,
                    "route": "local",
                }
            ]
        elif specialist_backend == "openrouter":
            specialist_model = str(
                specialist.get("model", "") or specialist.get("openrouter_model", "")
            ).strip()
            if not specialist_model:
                raise CLIError(
                    "E_MODEL",
                    f"OpenRouter specialist '{specialist.get('id', 'unknown')}' is missing model.",
                )
            model_candidates = [specialist_model]
            (
                result_content,
                usage,
                estimated_cost,
                selected_model,
                model_attempts,
                retry_count,
            ) = _run_openrouter_inference(
                project_root=project_root,
                messages=messages,
                model_candidates=model_candidates,
                max_tokens=runtime.max_output_tokens,
                max_retries=runtime.model_max_retries,
                retry_backoff_sec=runtime.model_retry_backoff_sec,
                route_label="openrouter-specialist",
            )
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
            total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))
        else:
            raise CLIError("E_MODEL", f"Unsupported specialist backend: {specialist_backend}")
    else:
        model_candidates = _ordered_models(runtime.default_model, runtime.model_fallbacks)
        (
            result_content,
            usage,
            estimated_cost,
            selected_model,
            model_attempts,
            retry_count,
        ) = _run_openrouter_inference(
            project_root=project_root,
            messages=messages,
            model_candidates=model_candidates,
            max_tokens=runtime.max_output_tokens,
            max_retries=runtime.model_max_retries,
            retry_backoff_sec=runtime.model_retry_backoff_sec,
            route_label="openrouter",
        )
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))

    if prompt_tokens > runtime.max_input_tokens:
        raise CLIError(
            "E_BUDGET",
            f"Model prompt tokens {prompt_tokens} exceeded max-input-tokens {runtime.max_input_tokens}.",
        )
    if completion_tokens > runtime.max_output_tokens:
        raise CLIError(
            "E_BUDGET",
            (
                f"Model completion tokens {completion_tokens} exceeded "
                f"max-output-tokens {runtime.max_output_tokens}."
            ),
        )
    if estimated_cost > runtime.max_cost_usd:
        raise CLIError(
            "E_BUDGET",
            f"Estimated cost ${estimated_cost:.6f} exceeded max-cost-usd {runtime.max_cost_usd:.6f}.",
        )

    content = result_content
    agent_plan = _normalize_agent_plan(content)
    if no_apply:
        apply_report = {
            "files_written": [],
            "files_written_count": 0,
            "bootstrap_languages": [],
            "dependencies_install": [],
            "post_commands": [],
            "no_apply": True,
        }
    else:
        apply_report = _apply_agent_plan(
            project_root=project_root,
            task=task,
            plan=agent_plan,
        )
    diff_touched = _extract_diff_file_paths(content)
    files_touched = sorted(set(diff_touched + list(apply_report.get("files_written", []))))
    code_warnings: list[str] = []
    if agent_plan.get("raw_format") != "json":
        code_warnings.append(
            "Model output was not strict JSON; apply-to-disk used fallback behavior."
        )
    elif not _plan_has_file_writes(agent_plan):
        code_warnings.append(
            "Structured plan contained no files; nothing was written unless bootstrap defaults were applied."
        )

    dep_installs = apply_report.get("dependencies_install", [])
    if isinstance(dep_installs, list):
        failed_installs = [
            item
            for item in dep_installs
            if isinstance(item, dict) and not bool(item.get("ok", False))
        ]
        for item in failed_installs:
            cmd = str(item.get("command", "")).strip() or "<unknown>"
            err = str(item.get("error", "")).strip() or str(item.get("stderr_tail", "")).strip()
            code_warnings.append(f"Dependency install failed: {cmd} ({err})")
    if no_apply:
        code_warnings.append("Apply-to-disk skipped (--no-apply).")
    if benchmark_parity:
        code_warnings.append(
            "Benchmark parity mode enabled; elephant-only session context compression is disabled."
        )
    if retry_count > 0:
        code_warnings.append(f"Model request recovered after {retry_count} retry attempt(s).")
    if routing["route"] == "openrouter" and selected_model != runtime.default_model:
        code_warnings.append(
            f"Primary model '{runtime.default_model}' failed; fallback model '{selected_model}' was used."
        )
    code_warnings.extend(route_warnings)
    code_warnings.extend(persona_warnings)

    return {
        "changes": [
            {
                "agent_id": "worker_1",
                "type": "model_output",
                "content": content,
            }
        ],
        "files_touched": files_touched,
        "agent_reports": [
            {
                "agent_id": "worker_1",
                "model": selected_model,
                "status": "completed",
                "summary": "OpenRouter response received.",
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
                "estimated_cost_usd": estimated_cost,
            }
        ],
        "selected_model": selected_model,
        "model_candidates": model_candidates,
        "retry_count": retry_count,
        "model_attempts": model_attempts,
        "routing": routing,
        "router_mode": router_mode,
        "requested_specialist": requested_specialist,
        "benchmark_parity": benchmark_parity,
        "verification_summary": (
            "Model output generated; apply-to-disk skipped (--no-apply)."
            if no_apply
            else (
                "Applied agent plan to disk with language bootstrap/dependency setup."
                if apply_report.get("files_written_count", 0) > 0
                else "No file writes applied from agent output."
            )
        ),
        "task": task,
        "dry_run": False,
        "no_apply": no_apply,
        "mode": mode,
        "project_root": str(project_root),
        "active_persona": active_persona,
        "index_stats": index_stats,
        "impact_report": impact,
        "context_profile": profile_name,
        "context_manifest": context_manifest,
        "agent_plan_summary": str(agent_plan.get("summary", "")),
        "apply_report": apply_report,
        "_warnings": code_warnings,
        "_response_metrics": {
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost,
        },
    }


def _command_agents(_: argparse.Namespace, project_root: Path) -> dict[str, Any]:
    """Agents command with OpenRouter + local specialist visibility."""
    cfg = load_config(project_root)
    default_model = str(cfg.get("model.default", "gpt-4o-mini"))
    specialists = _normalized_specialists(project_root)
    ready_count = sum(1 for item in specialists if bool(item.get("ready", False)))
    enabled_count = sum(1 for item in specialists if bool(item.get("enabled", False)))
    return {
        "agents": [
            {
                "agent_id": "orchestrator",
                "role": "main_ai",
                "status": "ready",
                "shared_context": "global_context",
            },
            {
                "agent_id": "worker_template",
                "role": "coder",
                "status": "idle",
                "private_context": "agent_context",
            },
        ],
        "local_specialists": specialists,
        "local_specialists_summary": {
            "configured": len(specialists),
            "enabled": enabled_count,
            "ready": ready_count,
            "registry_path": _gguf_registry_path(project_root).as_posix(),
        },
        "routing_policy": {
            "default_model": default_model,
            "strategy": "token_first_moe_auto",
            "supports_routes": ["auto", "openrouter", "local"],
            "local_enabled": enabled_count > 0,
            "local_ready": ready_count > 0,
        },
        "default_model": default_model,
    }


def _command_persona(args: argparse.Namespace, project_root: Path) -> dict[str, Any]:
    """Persona command with prompt ingestion and active-persona management."""
    personas_dir = project_root / ".elephant-coder" / "personas"
    available_before = sorted(path.name for path in personas_dir.glob("*.md"))

    ingest_file = str(getattr(args, "ingest_file", "") or "").strip()
    store_name = str(getattr(args, "store_name", "") or "").strip() or None
    activate_after_ingest = bool(getattr(args, "activate", False))
    set_active = str(getattr(args, "set_active", "") or "").strip()
    ingest: dict[str, Any] | None = None

    if ingest_file:
        ingest = _ingest_prompt_markdown_file(
            project_root=project_root,
            source_path=ingest_file,
            store_name=store_name,
            activate=activate_after_ingest,
        )

    available = sorted(path.name for path in personas_dir.glob("*.md"))
    active: str | None = None
    if set_active:
        requested = _persona_file_from_name(set_active)
        if requested not in available:
            raise CLIError("E_CONFIG", f"Persona not found: {set_active}")
        _write_text_if_changed(_active_persona_marker_path(project_root), requested + "\n")
        active = requested
    elif ingest and bool(ingest.get("activate_applied", False)):
        active = str(ingest["persona_file"])
    elif args.persona:
        requested = _persona_file_from_name(str(args.persona))
        if requested in available:
            active = requested
    if active is None:
        active = _read_active_persona(project_root, available)
    if active is None and "default.md" in available:
        active = "default.md"
    if active is None and available:
        active = available[0]

    library = _load_prompt_library_index(project_root)
    library_items = library.get("items", [])
    if not isinstance(library_items, list):
        library_items = []

    validation_note = "Persona storage and selection are active."
    if ingest:
        validation_note = "Prompt ingestion completed and persona asset stored."
    elif available_before != available:
        validation_note = "Persona list updated."

    data: dict[str, Any] = {
        "active_persona": active,
        "available_personas": available,
        "prompt_library": {
            "count": len(library_items),
            "index_path": _prompt_library_index_path(project_root).as_posix(),
        },
        "validation": {
            "status": "ok",
            "note": validation_note,
        },
    }
    if ingest:
        data["ingest"] = ingest
    return {
        **data,
    }


def _command_plugins(args: argparse.Namespace, project_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Plugins command scaffold."""
    plugins_dir = project_root / ".elephant-coder" / "plugins"
    plugins = sorted(path.name for path in plugins_dir.iterdir() if path.is_dir())
    requested = list(getattr(args, "permissions", []) or [])
    granted_cfg = config.get("plugins.allowed_permissions", [])
    if isinstance(granted_cfg, str):
        granted = [granted_cfg]
    else:
        granted = list(granted_cfg)
    return {
        "plugins": plugins,
        "requested_permissions": requested,
        "granted_permissions": granted,
    }


def _command_git(_: argparse.Namespace, project_root: Path) -> dict[str, Any]:
    """Git command with index-backed impact summary."""
    status_text, changed_files, err = _git_status(project_root)
    index = _new_index_service(project_root)
    try:
        index_stats = index.refresh_index()
        impact = index.impact_for_files(_changed_python_files(project_root, changed_files))
    finally:
        index.close()

    return {
        "repo_status": status_text,
        "changed_files": changed_files,
        "impact_report": impact,
        "index_stats": index_stats,
        "error": err,
    }


def _safe_int(value: Any, default: int = 0) -> int:
    """Convert value to int with fallback."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float with fallback."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _benchmark_results_path(project_root: Path) -> Path:
    """Return benchmark results path."""
    return project_root / ".elephant-coder" / "runs" / "benchmark_results.json"


def _load_benchmark_summary(project_root: Path) -> dict[str, Any] | None:
    """Load compact benchmark summary if benchmark artifacts exist."""
    path = _benchmark_results_path(project_root)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None

    aggregates = payload.get("aggregates", {})
    if not isinstance(aggregates, dict):
        aggregates = {}
    out = {
        "path": path.as_posix(),
        "generated_at_utc": str(payload.get("generated_at_utc", "")),
        "tasks_total": _safe_int(payload.get("tasks_total", 0)),
        "runs_total": _safe_int(payload.get("runs_total", 0)),
        "token_reduction_pct": _safe_float(aggregates.get("token_reduction_pct", 0.0)),
        "quality_delta_pct_points": _safe_float(
            aggregates.get("quality_delta_pct_points", 0.0)
        ),
        "latency_delta_ms": _safe_int(aggregates.get("latency_delta_ms", 0)),
    }
    baseline = aggregates.get("baseline", {})
    elephant = aggregates.get("elephant", {})
    if isinstance(baseline, dict):
        out["baseline_success_rate"] = _safe_float(baseline.get("success_rate", 0.0))
    if isinstance(elephant, dict):
        out["elephant_success_rate"] = _safe_float(elephant.get("success_rate", 0.0))
    return out


def _collect_reliability_metrics(run_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute reliability metrics from recorded /code runs."""
    code_runs = 0
    code_ok = 0
    retry_recovered_runs = 0
    fallback_runs = 0
    total_retry_count = 0
    attempts_total = 0
    attempts_success = 0
    attempts_failed = 0
    error_codes: dict[str, int] = {}
    per_model: dict[str, dict[str, int]] = {}
    route_counts: dict[str, int] = {}

    for payload in run_payloads:
        if str(payload.get("command", "")) != "/code":
            continue
        code_runs += 1
        ok = bool(payload.get("ok", False))
        if ok:
            code_ok += 1

        for err in payload.get("errors", []) or []:
            if isinstance(err, dict):
                code = str(err.get("code", "")).strip() or "E_UNKNOWN"
                error_codes[code] = error_codes.get(code, 0) + 1

        data = payload.get("data", {})
        if not isinstance(data, dict):
            continue
        routing = data.get("routing", {})
        if isinstance(routing, dict):
            route = str(routing.get("route", "")).strip()
            if route:
                route_counts[route] = route_counts.get(route, 0) + 1

        retry_count = _safe_int(data.get("retry_count", 0))
        total_retry_count += max(0, retry_count)
        if ok and retry_count > 0:
            retry_recovered_runs += 1

        runtime = data.get("runtime", {})
        default_model = ""
        if isinstance(runtime, dict):
            default_model = str(runtime.get("model", "")).strip()
        selected_model = str(data.get("selected_model", "")).strip() or default_model
        if default_model and selected_model and selected_model != default_model:
            fallback_runs += 1

        attempts = data.get("model_attempts", [])
        if not isinstance(attempts, list):
            attempts = []
        if not attempts and selected_model:
            attempts = [
                {
                    "model": selected_model,
                    "success": bool(ok),
                }
            ]
        for attempt in attempts:
            if not isinstance(attempt, dict):
                continue
            model = str(attempt.get("model", "")).strip() or "unknown"
            success = bool(attempt.get("success", False))
            stats = per_model.setdefault(model, {"attempts": 0, "success": 0, "failed": 0})
            stats["attempts"] += 1
            attempts_total += 1
            if success:
                stats["success"] += 1
                attempts_success += 1
            else:
                stats["failed"] += 1
                attempts_failed += 1

    for value in per_model.values():
        attempts = int(value.get("attempts", 0))
        success = int(value.get("success", 0))
        value["success_rate"] = round((success / attempts) * 100.0, 2) if attempts else 0.0

    return {
        "code_runs_total": code_runs,
        "code_runs_ok": code_ok,
        "code_success_rate": round((code_ok / code_runs) * 100.0, 2) if code_runs else 0.0,
        "retry_recovered_runs": retry_recovered_runs,
        "fallback_runs": fallback_runs,
        "total_retry_count": total_retry_count,
        "model_attempts_total": attempts_total,
        "model_attempts_success": attempts_success,
        "model_attempts_failed": attempts_failed,
        "model_attempt_success_rate": (
            round((attempts_success / attempts_total) * 100.0, 2) if attempts_total else 0.0
        ),
        "error_codes": error_codes,
        "per_model": per_model,
        "route_counts": route_counts,
    }


def _command_stats(project_root: Path) -> dict[str, Any]:
    """Stats command scaffold using persisted run records."""
    runs_dir = project_root / ".elephant-coder" / "runs"
    total_runs = 0
    total_tokens = 0
    total_cost = 0.0
    run_payloads: list[dict[str, Any]] = []
    for rec in runs_dir.glob("*.json"):
        try:
            payload = json.loads(rec.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        run_payloads.append(payload)
        total_runs += 1
        metrics = payload.get("metrics", {})
        total_tokens += _safe_int(metrics.get("total_tokens", 0))
        total_cost += _safe_float(metrics.get("estimated_cost_usd", 0.0))

    index = _new_index_service(project_root)
    try:
        index_counts = index.index_stats()
    finally:
        index.close()

    reliability_metrics = _collect_reliability_metrics(run_payloads)
    benchmark_summary = _load_benchmark_summary(project_root)
    quality_note = "Quality benchmarking is defined in BENCHMARK_PROTOCOL.md."
    if benchmark_summary is not None:
        quality_note = "Benchmark summary loaded from benchmark_results.json."

    return {
        "token_metrics": {
            "total_tokens": total_tokens,
            "avg_tokens_per_run": int(total_tokens / total_runs) if total_runs else 0,
        },
        "cost_metrics": {
            "total_cost_usd": round(total_cost, 6),
            "avg_cost_per_run_usd": round(total_cost / total_runs, 6) if total_runs else 0.0,
        },
        "latency_metrics": {
            "note": "Per-command latency tracking present in run records.",
        },
        "quality_metrics": {
            "note": quality_note,
            "benchmark_summary": benchmark_summary,
        },
        "reliability_metrics": reliability_metrics,
        "memory_metrics": {
            "project_storage": str(project_root / ".elephant-coder"),
            "runs_recorded": total_runs,
        },
        "index_metrics": index_counts,
    }


def _command_test(args: argparse.Namespace, project_root: Path) -> dict[str, Any]:
    """Select tests from changed/impacted files."""
    task = args.task or "No task provided."
    _, changed_files, _ = _git_status(project_root)

    index = _new_index_service(project_root)
    try:
        index.refresh_index()
        impact = index.impact_for_files(_changed_python_files(project_root, changed_files))
    finally:
        index.close()

    impacted = [item["file_path"] for item in impact["impacted"]]
    selected: list[str] = []
    for file_path in impacted:
        if file_path.startswith("tests/") and file_path.endswith(".py"):
            selected.append(file_path)

    if not selected:
        for file_path in impacted:
            if not file_path.endswith(".py"):
                continue
            stem = Path(file_path).stem
            candidate = project_root / "tests" / f"test_{stem}.py"
            if candidate.exists():
                selected.append(candidate.relative_to(project_root).as_posix())

    selected = sorted(set(selected))[:25]
    return {
        "tests_selected": selected,
        "tests_run": [],
        "results": {
            "status": "selected_only",
            "summary": "Selection is impact-aware; execution wiring is pending.",
        },
        "impact_report": impact,
        "task": task,
    }


def _execute_handler(
    args: argparse.Namespace,
    project_root: Path,
    config: dict[str, Any],
    runtime: RuntimeConfig,
    session_id: str,
) -> tuple[dict[str, Any], list[str]]:
    """Dispatch command handlers and return data/warnings."""
    cmd = args.command
    warnings: list[str] = []
    setattr(args, "_runtime", runtime)
    setattr(args, "_session_id", session_id)
    if cmd == "plan":
        return _command_plan(args, project_root), warnings
    if cmd == "code":
        return _command_code(args, project_root), warnings
    if cmd == "agents":
        warnings.append("Agent lifecycle and OpenRouter dispatch remain scaffold-only in current phase.")
        return _command_agents(args, project_root), warnings
    if cmd == "persona":
        warnings.append("Persona guidance is applied in /code prompts; full schema validation is still basic.")
        return _command_persona(args, project_root), warnings
    if cmd == "plugins":
        warnings.append("Plugin execution runtime is not fully wired yet; reporting mode only.")
        return _command_plugins(args, project_root, config), warnings
    if cmd == "git":
        return _command_git(args, project_root), warnings
    if cmd == "stats":
        return _command_stats(project_root), warnings
    if cmd == "test":
        return _command_test(args, project_root), warnings
    raise ValueError(f"Unknown command: {cmd}")


def execute_command(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    """Execute a parsed command and return (exit_code, response)."""
    t0 = time.perf_counter()
    cwd = Path(args.cwd or ".").resolve()
    project_root = detect_project_root(cwd)
    base = ensure_project_layout(project_root)
    config = load_config(project_root)
    runtime = resolve_runtime_config(args, config)

    errors: list[dict[str, str]] = []
    if runtime.max_input_tokens <= 0 or runtime.max_output_tokens <= 0 or runtime.max_cost_usd <= 0:
        errors.append(
            {
                "code": "E_BUDGET",
                "message": "Budget values must be > 0.",
            }
        )

    if runtime.output not in {"text", "json"}:
        errors.append(
            {
                "code": "E_CONFIG",
                "message": "Invalid output mode. Expected 'text' or 'json'.",
            }
        )

    session_id = args.session or _make_id("sess")
    run_id = _make_id("run")

    if errors:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        response = _build_response(
            ok=False,
            command=f"/{args.command}",
            run_id=run_id,
            session_id=session_id,
            data={},
            warnings=[],
            errors=errors,
            latency_ms=latency_ms,
        )
        try:
            _write_run_record(base, response)
        except Exception:
            pass
        return 2, response

    try:
        data, warnings = _execute_handler(args, project_root, config, runtime, session_id)
        extra_warnings = data.pop("_warnings", None)
        if isinstance(extra_warnings, list):
            warnings.extend(str(item) for item in extra_warnings if str(item).strip())
        response_metrics = data.pop("_response_metrics", None)
        # Include resolved runtime so command behavior is inspectable.
        data["runtime"] = {
            "resolved_at_utc": _utc_now_iso(),
            "model": runtime.default_model,
            "model_fallbacks": list(runtime.model_fallbacks),
            "model_max_retries": runtime.model_max_retries,
            "model_retry_backoff_sec": runtime.model_retry_backoff_sec,
            "max_input_tokens": runtime.max_input_tokens,
            "max_output_tokens": runtime.max_output_tokens,
            "max_cost_usd": runtime.max_cost_usd,
            "project_root": str(project_root),
        }
        latency_ms = int((time.perf_counter() - t0) * 1000)
        response = _build_response(
            ok=True,
            command=f"/{args.command}",
            run_id=run_id,
            session_id=session_id,
            data=data,
            warnings=warnings,
            errors=[],
            latency_ms=latency_ms,
            metrics=response_metrics,
        )
        if args.command == "code":
            task_text = str(getattr(args, "task", "") or "").strip()
            if task_text:
                _append_session_event(
                    project_root,
                    session_id,
                    "user",
                    task_text,
                    command="/code",
                    run_id=run_id,
                )
            assistant_text = ""
            changes = data.get("changes", [])
            if isinstance(changes, list) and changes:
                first = changes[0]
                if isinstance(first, dict):
                    assistant_text = str(first.get("content", "") or "").strip()
            if not assistant_text:
                assistant_text = str(data.get("verification_summary", "") or "").strip()
            if assistant_text:
                _append_session_event(
                    project_root,
                    session_id,
                    "assistant",
                    assistant_text,
                    command="/code",
                    run_id=run_id,
                )
        _write_run_record(base, response)
        return 0, response
    except CLIError as exc:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        response = _build_response(
            ok=False,
            command=f"/{args.command}",
            run_id=run_id,
            session_id=session_id,
            data={},
            warnings=[],
            errors=[{"code": exc.code, "message": exc.message}],
            latency_ms=latency_ms,
        )
        if args.command == "code":
            task_text = str(getattr(args, "task", "") or "").strip()
            if task_text:
                _append_session_event(
                    project_root,
                    session_id,
                    "user",
                    task_text,
                    command="/code",
                    run_id=run_id,
                )
            _append_session_event(
                project_root,
                session_id,
                "assistant",
                f"error [{exc.code}]: {exc.message}",
                command="/code",
                run_id=run_id,
            )
        try:
            _write_run_record(base, response)
        except Exception:
            pass
        return 2, response
    except Exception as exc:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        response = _build_response(
            ok=False,
            command=f"/{args.command}",
            run_id=run_id,
            session_id=session_id,
            data={},
            warnings=[],
            errors=[{"code": "E_STORAGE", "message": str(exc)}],
            latency_ms=latency_ms,
        )
        if args.command == "code":
            task_text = str(getattr(args, "task", "") or "").strip()
            if task_text:
                _append_session_event(
                    project_root,
                    session_id,
                    "user",
                    task_text,
                    command="/code",
                    run_id=run_id,
                )
            _append_session_event(
                project_root,
                session_id,
                "assistant",
                f"error [E_STORAGE]: {exc}",
                command="/code",
                run_id=run_id,
            )
        try:
            _write_run_record(base, response)
        except Exception:
            pass
        return 1, response


def _print_text_response(response: dict[str, Any]) -> None:
    """Render response in compact human-readable form."""
    print(f"command: {response['command']}  ok: {response['ok']}")
    print(f"run: {response['run_id']}  session: {response['session_id']}")
    print(
        "metrics: "
        f"tokens={response['metrics']['total_tokens']} "
        f"cost={response['metrics']['estimated_cost_usd']:.6f} "
        f"latency_ms={response['metrics']['latency_ms']}"
    )
    if response["warnings"]:
        print("warnings:")
        for warning in response["warnings"]:
            print(f"- {warning}")
    if response["errors"]:
        print("errors:")
        for err in response["errors"]:
            print(f"- {err['code']}: {err['message']}")
    if response.get("data"):
        print("data:")
        print(json.dumps(response["data"], indent=2))


def _build_parser() -> argparse.ArgumentParser:
    """Construct CLI parser."""
    parser = argparse.ArgumentParser(
        prog="elephant",
        description="Elephant Coder CLI (Phase 1 scaffold)",
    )
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--output", choices=["text", "json"], default=None)
    shared.add_argument("--cwd", default=".")
    shared.add_argument("--session", default=None)
    shared.add_argument("--persona", default=None)
    shared.add_argument("--task", default=None)
    shared.add_argument("--max-input-tokens", type=int, default=None)
    shared.add_argument("--max-output-tokens", type=int, default=None)
    shared.add_argument("--max-cost-usd", type=float, default=None)

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", parents=[shared], help="Generate implementation plan.")
    code_p = sub.add_parser("code", parents=[shared], help="Execute coding flow.")
    code_p.add_argument("--dry-run", action="store_true", default=False)
    code_p.add_argument(
        "--no-apply",
        action="store_true",
        default=False,
        help="Run model inference but do not write files to disk.",
    )
    code_p.add_argument("--mode", choices=["elephant", "baseline"], default="elephant")
    code_p.add_argument("--router", choices=["auto", "openrouter", "local"], default="auto")
    code_p.add_argument(
        "--specialist",
        default=None,
        help="Specialist id/role for --router local (supports local and OpenRouter-backed specialists).",
    )
    code_p.add_argument(
        "--benchmark-parity",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS,
    )
    sub.add_parser("agents", parents=[shared], help="Manage/list coding agents.")
    persona_p = sub.add_parser("persona", parents=[shared], help="Inspect/select personas.")
    persona_p.add_argument("--ingest-file", default=None, help="Path to markdown prompt file to dissect/store.")
    persona_p.add_argument("--store-name", default=None, help="Persona name for stored prompt asset.")
    persona_p.add_argument("--activate", action="store_true", default=False, help="Activate persona after ingest.")
    persona_p.add_argument("--set-active", default=None, help="Set active persona by name.")
    plugins = sub.add_parser("plugins", parents=[shared], help="Manage plugins.")
    plugins.add_argument("--permissions", nargs="*", default=None)
    sub.add_parser("git", parents=[shared], help="Git summary + impact scaffold.")
    sub.add_parser("stats", parents=[shared], help="Run and budget statistics.")
    sub.add_parser("test", parents=[shared], help="Run/select tests.")
    sub.add_parser("shell", parents=[shared], help="Interactive slash-command shell.")
    session_p = sub.add_parser("session", parents=[shared], help="Interactive coding session.")
    session_p.add_argument("--dry-run", action="store_true", default=False)
    session_p.add_argument("--mode", choices=["elephant", "baseline"], default="elephant")
    session_p.add_argument("--router", choices=["auto", "openrouter", "local"], default="auto")
    session_p.add_argument("--specialist", default=None)
    return parser


def _parse(parser: argparse.ArgumentParser, argv: list[str]) -> argparse.Namespace:
    """Parse argv after slash normalization."""
    return parser.parse_args(_normalize_argv(argv))


def _rewrite_interactive_command_parts(parts: list[str]) -> list[str]:
    """Support shorthand in interactive mode, e.g. `/code hello`."""
    if not parts:
        return parts
    raw_cmd = str(parts[0] or "")
    cmd = raw_cmd[1:] if raw_cmd.startswith("/") else raw_cmd
    cmd = cmd.strip().lower()
    if cmd not in {"code", "plan"}:
        return parts

    has_task_flag = any(item == "--task" or str(item).startswith("--task=") for item in parts[1:])
    if has_task_flag:
        return parts
    if len(parts) <= 1:
        return parts

    # Safe shorthand rewrite only when all trailing tokens are plain text.
    trailing = parts[1:]
    if any(str(tok).startswith("-") for tok in trailing):
        return parts
    return [parts[0], "--task", " ".join(str(tok) for tok in trailing)]


def _run_shell(shell_args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Interactive shell for slash commands."""
    print("Elephant shell. Use /plan, /code, /agents, /persona, /plugins, /git, /stats, /test.")
    print("Type 'exit' or 'quit' to stop.")
    active_session = shell_args.session or _make_id("sess")

    base_defaults = {
        "cwd": shell_args.cwd,
        "session": active_session,
        "persona": shell_args.persona,
        "output": shell_args.output,
        "max_input_tokens": shell_args.max_input_tokens,
        "max_output_tokens": shell_args.max_output_tokens,
        "max_cost_usd": shell_args.max_cost_usd,
    }

    while True:
        try:
            line = input("elephant> ").strip()
        except EOFError:
            return 0
        if not line:
            continue
        if line.lower() in {"exit", "quit"}:
            return 0

        try:
            parts = shlex.split(line)
        except ValueError as exc:
            print(f"parse error: {exc}")
            continue
        if not parts:
            continue
        parts = _rewrite_interactive_command_parts(parts)

        try:
            cmd_args = _parse(parser, parts)
            if cmd_args.command == "shell":
                print("Nested shell is not supported.")
                continue
            if cmd_args.command == "code" and not str(getattr(cmd_args, "task", "") or "").strip():
                print("code task required. use /code <task> or /code --task <task>.")
                continue
            for key, value in base_defaults.items():
                if getattr(cmd_args, key, None) is None:
                    setattr(cmd_args, key, value)
            code, response = execute_command(cmd_args)
            out_mode = getattr(cmd_args, "output", None) or "text"
            if out_mode == "json":
                print(json.dumps(response, indent=2))
            else:
                _print_text_response(response)
            if code not in {0, 2}:
                # Keep shell alive while reporting failures.
                print(f"command exited with code {code}")
        except SystemExit:
            print("invalid command usage")
            continue


def _print_session_turn(response: dict[str, Any]) -> None:
    """Render concise turn output for interactive coding sessions."""
    if not response.get("ok", False):
        for err in response.get("errors", []):
            print(f"error [{err.get('code', 'E_UNKNOWN')}]: {err.get('message', '')}")
        return

    data = response.get("data", {})
    changes = data.get("changes", [])
    content = ""
    if isinstance(changes, list) and changes:
        first = changes[0]
        if isinstance(first, dict):
            content = str(first.get("content", "") or "").strip()
    if content:
        print(content)
    else:
        print(str(data.get("verification_summary", "No output.")))

    files = data.get("files_touched", []) or []
    if files:
        preview = ", ".join(str(item) for item in files[:8])
        if len(files) > 8:
            preview += ", ..."
        print(f"\nfiles: {preview}")

    metrics = response.get("metrics", {}) or {}
    print(
        f"tokens={int(metrics.get('total_tokens', 0))} "
        f"cost={float(metrics.get('estimated_cost_usd', 0.0)):.6f} "
        f"latency_ms={int(metrics.get('latency_ms', 0))}"
    )


def _run_session(session_args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Interactive coding session: plain prompts route to /code."""
    active_session = session_args.session or _make_id("sess")
    print(f"Elephant session: {active_session}")
    print("Enter a coding request directly. Use /help for commands, /exit to quit.")

    base_defaults = {
        "cwd": session_args.cwd,
        "session": active_session,
        "persona": session_args.persona,
        "output": session_args.output or "text",
        "mode": session_args.mode,
        "router": session_args.router,
        "specialist": session_args.specialist,
        "max_input_tokens": session_args.max_input_tokens,
        "max_output_tokens": session_args.max_output_tokens,
        "max_cost_usd": session_args.max_cost_usd,
    }

    while True:
        try:
            line = input("elephant(session)> ").strip()
        except EOFError:
            return 0
        if not line:
            continue

        low = line.lower()
        if low in {"exit", "quit", "/exit", "/quit"}:
            return 0
        if low in {"/help", "help"}:
            print("Session commands: /exit, /quit, /help, /plan, /git, /test, /stats.")
            print("Any non-slash line is treated as /code --task \"...\".")
            continue

        if line.startswith("/"):
            try:
                parts = shlex.split(line)
            except ValueError as exc:
                print(f"parse error: {exc}")
                continue
            if not parts:
                continue
            parts = _rewrite_interactive_command_parts(parts)
        else:
            parts = ["code", "--task", line]
            if bool(getattr(session_args, "dry_run", False)):
                parts.append("--dry-run")
            if str(getattr(session_args, "mode", "elephant")) != "elephant":
                parts.extend(["--mode", str(session_args.mode)])
            if str(getattr(session_args, "router", "auto")) != "auto":
                parts.extend(["--router", str(session_args.router)])
            if str(getattr(session_args, "specialist", "") or "").strip():
                parts.extend(["--specialist", str(session_args.specialist)])

        try:
            has_mode_flag = any(
                item == "--mode" or str(item).startswith("--mode=") for item in parts
            )
            has_router_flag = any(
                item == "--router" or str(item).startswith("--router=") for item in parts
            )
            has_specialist_flag = any(
                item == "--specialist" or str(item).startswith("--specialist=") for item in parts
            )
            cmd_args = _parse(parser, parts)
            if cmd_args.command in {"session", "shell"}:
                print("Nested interactive mode is not supported.")
                continue
            if cmd_args.command == "code" and not str(getattr(cmd_args, "task", "") or "").strip():
                print("code task required. use /code <task> or /code --task <task>.")
                continue
            for key, value in base_defaults.items():
                if getattr(cmd_args, key, None) is None:
                    setattr(cmd_args, key, value)
            if (
                cmd_args.command == "code"
                and not has_mode_flag
                and str(getattr(session_args, "mode", "elephant")) != "elephant"
            ):
                setattr(cmd_args, "mode", str(session_args.mode))
            if (
                cmd_args.command == "code"
                and not has_router_flag
                and str(getattr(session_args, "router", "auto")) != "auto"
            ):
                setattr(cmd_args, "router", str(session_args.router))
            if (
                cmd_args.command == "code"
                and not has_specialist_flag
                and str(getattr(session_args, "specialist", "") or "").strip()
            ):
                setattr(cmd_args, "specialist", str(session_args.specialist))

            code, response = execute_command(cmd_args)
            out_mode = getattr(cmd_args, "output", None) or "text"
            if out_mode == "json":
                print(json.dumps(response, indent=2))
            elif cmd_args.command == "code":
                _print_session_turn(response)
            else:
                _print_text_response(response)
            if code not in {0, 2}:
                print(f"command exited with code {code}")
        except SystemExit:
            print("invalid command usage")
            continue


def run_cli(argv: list[str] | None = None) -> tuple[int, dict[str, Any] | None]:
    """Run CLI programmatically and return (exit_code, optional_response)."""
    if argv is None:
        argv = sys.argv[1:]
    parser = _build_parser()
    args = _parse(parser, argv)
    if args.command == "shell":
        code = _run_shell(args, parser)
        return code, None
    if args.command == "session":
        code = _run_session(args, parser)
        return code, None
    code, response = execute_command(args)
    out_mode = args.output or "text"
    if out_mode == "json":
        print(json.dumps(response, indent=2))
    else:
        _print_text_response(response)
    return code, response


def main() -> None:
    """CLI entry point."""
    try:
        code, _ = run_cli()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        code = 130
    except SystemExit:
        raise
    except Exception as exc:
        payload = {
            "ok": False,
            "command": "/unknown",
            "run_id": _make_id("run"),
            "session_id": _make_id("sess"),
            "data": {},
            "metrics": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "latency_ms": 0,
            },
            "warnings": [],
            "errors": [{"code": "E_STORAGE", "message": str(exc)}],
        }
        print(json.dumps(payload, indent=2), file=sys.stderr)
        code = 1
    raise SystemExit(code)


if __name__ == "__main__":
    main()
