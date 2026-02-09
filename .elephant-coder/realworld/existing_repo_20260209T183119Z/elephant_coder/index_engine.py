"""Incremental Python indexing and file-level impact analysis."""

from __future__ import annotations

import ast
import hashlib
import time
from collections import deque
from pathlib import Path
from typing import Any

from .state_store import StateStore

_SKIP_DIRS = {
    ".elephant-coder",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
}


def _sha256_text(value: str) -> str:
    """Return sha256 hex digest for text input."""
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _normalize_rel(path: Path, project_root: Path) -> str:
    """Normalize path to project-relative POSIX style."""
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def _safe_unparse(node: ast.AST | None) -> str:
    """Unparse AST node if possible."""
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _extract_imports(tree: ast.Module) -> list[str]:
    """Extract module-level imports."""
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    out.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    if module:
                        out.add(module)
                elif module:
                    out.add(f"{module}.{alias.name}")
                else:
                    out.add(alias.name)
    return sorted(out)


class _Collector(ast.NodeVisitor):
    """Collect symbols and call references."""

    def __init__(self):
        self.scope: list[str] = []
        self.symbols: list[dict[str, Any]] = []
        self.calls: list[dict[str, str]] = []

    def _qualname(self, name: str) -> str:
        if not self.scope:
            return name
        return ".".join([*self.scope, name])

    def _record_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        kind: str,
    ) -> None:
        signature = self._function_signature(node, kind)
        qual = self._qualname(node.name)
        self.symbols.append(
            {
                "symbol_name": node.name,
                "qualname": qual,
                "kind": kind,
                "lineno": int(getattr(node, "lineno", 0)),
                "end_lineno": int(getattr(node, "end_lineno", getattr(node, "lineno", 0))),
                "signature": signature,
            }
        )
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    @staticmethod
    def _function_signature(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        kind: str,
    ) -> str:
        params: list[str] = []
        for arg in node.args.args:
            annotation = f": {_safe_unparse(arg.annotation)}" if arg.annotation else ""
            params.append(f"{arg.arg}{annotation}")
        if node.args.vararg is not None:
            params.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg is not None:
            params.append(f"**{node.args.kwarg.arg}")
        ret = f" -> {_safe_unparse(node.returns)}" if node.returns else ""
        prefix = "async def" if kind == "async_function" else "def"
        return f"{prefix} {node.name}({', '.join(params)}){ret}"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = ", ".join(_safe_unparse(base) for base in node.bases if _safe_unparse(base))
        signature = f"class {node.name}({bases})" if bases else f"class {node.name}"
        qual = self._qualname(node.name)
        self.symbols.append(
            {
                "symbol_name": node.name,
                "qualname": qual,
                "kind": "class",
                "lineno": int(getattr(node, "lineno", 0)),
                "end_lineno": int(getattr(node, "end_lineno", getattr(node, "lineno", 0))),
                "signature": signature,
            }
        )
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node, "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node, "async_function")

    def visit_Call(self, node: ast.Call) -> None:
        callee = ""
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr
        if callee:
            caller = ".".join(self.scope) if self.scope else "<module>"
            self.calls.append(
                {
                    "caller_qualname": caller,
                    "callee_name": callee,
                }
            )
        self.generic_visit(node)


def _parse_python_file(path: Path) -> tuple[list[dict[str, Any]], list[str], list[dict[str, str]], str | None]:
    """Parse one Python file into symbols/imports/calls and parse error."""
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, ValueError) as exc:
        return [], [], [], str(exc)

    collector = _Collector()
    collector.visit(tree)
    imports = _extract_imports(tree)
    return collector.symbols, imports, collector.calls, None


class IndexService:
    """Incremental index and impact engine for Elephant Coder."""

    def __init__(
        self,
        project_root: Path,
        *,
        world_model_enabled: bool = True,
        world_model_dim: int = 512,
        world_model_capsule_dim: int = 32,
        world_model_semantic_dims: int = 28,
        world_model_max_edge_facts: int = 20000,
        world_model_max_symbol_facts: int = 5000,
    ):
        self.project_root = project_root.resolve()
        self.store = StateStore(self.project_root / ".elephant-coder" / "state.db")
        self.world_model_enabled = bool(world_model_enabled)
        self.world_model_dim = max(64, int(world_model_dim))
        self.world_model_capsule_dim = max(0, int(world_model_capsule_dim))
        self.world_model_semantic_dims = max(1, int(world_model_semantic_dims))
        if (
            self.world_model_capsule_dim > 0
            and self.world_model_semantic_dims >= self.world_model_capsule_dim
        ):
            self.world_model_semantic_dims = max(1, self.world_model_capsule_dim - 4)
        self.world_model_max_edge_facts = max(0, int(world_model_max_edge_facts))
        self.world_model_max_symbol_facts = max(0, int(world_model_max_symbol_facts))

    def close(self) -> None:
        """Close state store."""
        self.store.close()

    def _iter_python_files(self) -> list[Path]:
        """Enumerate Python files under project root."""
        files: list[Path] = []
        for path in self.project_root.rglob("*.py"):
            rel_parts = set(path.resolve().relative_to(self.project_root).parts)
            if rel_parts.intersection(_SKIP_DIRS):
                continue
            files.append(path)
        files.sort()
        return files

    def _resolve_import_to_file(self, module_name: str) -> str | None:
        """Resolve import name to project-relative file path if local."""
        if not module_name:
            return None
        parts = module_name.split(".")
        candidates = [
            self.project_root.joinpath(*parts).with_suffix(".py"),
            self.project_root.joinpath(*parts, "__init__.py"),
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return _normalize_rel(candidate, self.project_root)
        return None

    def _rebuild_edges(self) -> int:
        """Rebuild full dependency graph from imports and calls."""
        edges: set[tuple[str, str, str, float]] = set()
        symbols_by_name = self.store.symbol_files_by_name()

        for row in self.store.list_imports():
            src = str(row["file_path"])
            dst = self._resolve_import_to_file(str(row["module_name"]))
            if dst and dst != src:
                edges.add((src, dst, "import", 1.0))

        for row in self.store.list_calls():
            src = str(row["file_path"])
            callee = str(row["callee_name"])
            for dst in symbols_by_name.get(callee, set()):
                if dst != src:
                    edges.add((src, dst, "call", 0.7))

        self.store.replace_edges(
            [
                {
                    "src_file": src,
                    "dst_file": dst,
                    "edge_type": edge_type,
                    "weight": weight,
                }
                for src, dst, edge_type, weight in sorted(edges)
            ]
        )
        return len(edges)

    def refresh_index(self) -> dict[str, Any]:
        """Run incremental indexing and graph rebuild."""
        t0 = time.perf_counter()
        previous = self.store.get_indexed_file_meta()
        current_files = self._iter_python_files()
        current_map = {_normalize_rel(path, self.project_root): path for path in current_files}

        files_deleted = 0
        for old_rel in sorted(set(previous).difference(current_map)):
            self.store.delete_file(old_rel)
            files_deleted += 1

        files_scanned = len(current_files)
        files_indexed = 0
        files_skipped = 0
        parse_errors = 0

        for rel, path in current_map.items():
            source = path.read_text(encoding="utf-8", errors="replace")
            file_hash = _sha256_text(source)
            mtime = float(path.stat().st_mtime)
            prev = previous.get(rel)
            if (
                prev
                and str(prev.get("file_hash")) == file_hash
                and float(prev.get("mtime", -1.0)) == mtime
                and prev.get("parse_error") in {None, ""}
            ):
                files_skipped += 1
                continue

            symbols, imports, calls, parse_error = _parse_python_file(path)
            self.store.upsert_indexed_file(
                file_path=rel,
                file_hash=file_hash,
                mtime=mtime,
                indexed_at=time.time(),
                parse_error=parse_error,
            )
            self.store.replace_file_analysis(rel, symbols, imports, calls)
            files_indexed += 1
            if parse_error is not None:
                parse_errors += 1

        edges_total = self._rebuild_edges()
        counts = self.store.get_counts()
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "files_scanned": files_scanned,
            "files_indexed": files_indexed,
            "files_skipped": files_skipped,
            "files_deleted": files_deleted,
            "parse_errors": parse_errors,
            "symbols_total": counts["symbols"],
            "edges_total": edges_total,
            "elapsed_ms": elapsed_ms,
        }

    def _build_cognitive_world(self) -> tuple[Any | None, dict[str, Any]]:
        """Build a cognitive world model from indexed code facts."""
        summary_base = {
            "enabled": False,
            "error": None,
            "facts": 0,
            "expectations": 0,
            "edge_facts": 0,
            "symbol_facts": 0,
            "symbol_facts_truncated": 0,
            "capsule_enabled": self.world_model_capsule_dim > 0,
            "capsule_dim": self.world_model_capsule_dim,
            "semantic_dims": self.world_model_semantic_dims,
            "dim": self.world_model_dim,
            "max_edge_facts": self.world_model_max_edge_facts,
            "max_symbol_facts": self.world_model_max_symbol_facts,
            "capsule_active": False,
        }

        if not self.world_model_enabled:
            summary_base["error"] = "disabled by config"
            return None, summary_base

        try:
            import grilly.experimental.cognitive as cognitive
        except Exception as exc:
            fail = dict(summary_base)
            fail["error"] = f"cognitive import failed: {exc}"
            return None, fail

        try:
            world = cognitive.WorldModel(  # type: ignore[attr-defined]
                dim=self.world_model_dim,
                capsule_dim=self.world_model_capsule_dim,
                semantic_dims=self.world_model_semantic_dims,
            )
        except Exception as exc:
            fail = dict(summary_base)
            fail["error"] = f"world model init failed: {exc}"
            return None, fail

        edge_facts = 0
        for edge in self.store.list_edges()[: self.world_model_max_edge_facts]:
            src = str(edge["src_file"])
            dst = str(edge["dst_file"])
            edge_type = str(edge["edge_type"])
            strength = float(edge["weight"])
            relation = "imports" if edge_type == "import" else "calls"
            world.add_fact(
                subject=f"file:{src}",
                relation=relation,
                object_=f"file:{dst}",
                confidence=max(0.2, min(1.0, strength)),
                source="index",
            )
            world.add_causal_link(
                cause=f"file:{src}",
                effect=f"file:{dst}",
                strength=max(0.2, min(1.0, strength)),
            )
            edge_facts += 1

        all_symbols = self.store.list_symbols()
        symbol_limit = self.world_model_max_symbol_facts
        symbol_facts = 0
        for sym in all_symbols[:symbol_limit]:
            file_path = str(sym["file_path"])
            qualname = str(sym["qualname"])
            world.add_fact(
                subject=f"file:{file_path}",
                relation="contains",
                object_=f"symbol:{qualname}",
                confidence=0.9,
                source="index",
            )
            symbol_facts += 1

        ok = dict(summary_base)
        ok.update(
            {
                "enabled": True,
                "error": None,
                "facts": int(len(world.facts)),
                "expectations": int(len(world.expectations)),
                "edge_facts": edge_facts,
                "symbol_facts": symbol_facts,
                "symbol_facts_truncated": max(0, len(all_symbols) - symbol_facts),
                "capsule_active": bool(getattr(world, "capsule_encoder", None) is not None),
            }
        )
        return world, ok

    def impact_for_files(self, changed_files: list[str], max_depth: int = 8) -> dict[str, Any]:
        """Compute direct and transitive impact from changed files."""
        normalized = []
        indexed_files = set(self.store.get_indexed_file_meta().keys())
        for item in changed_files:
            norm = str(item).replace("\\", "/").strip()
            if norm in indexed_files:
                normalized.append(norm)
                continue
            absolute = Path(norm)
            if absolute.is_absolute():
                try:
                    rel = absolute.resolve().relative_to(self.project_root).as_posix()
                except ValueError:
                    rel = None
                if rel and rel in indexed_files:
                    normalized.append(rel)
                    continue
        changed = sorted(set(normalized))

        edges = self.store.list_edges()
        reverse: dict[str, list[tuple[str, str, float]]] = {}
        for edge in edges:
            src = str(edge["src_file"])
            dst = str(edge["dst_file"])
            edge_type = str(edge["edge_type"])
            weight = float(edge["weight"])
            reverse.setdefault(dst, []).append((src, edge_type, weight))

        distance: dict[str, int] = {}
        frontier = deque()
        for file_path in changed:
            distance[file_path] = 0
            frontier.append(file_path)

        while frontier:
            cur = frontier.popleft()
            cur_dist = distance[cur]
            if cur_dist >= max_depth:
                continue
            for dep, _, _ in reverse.get(cur, []):
                if dep not in distance:
                    distance[dep] = cur_dist + 1
                    frontier.append(dep)

        static_distance = dict(distance)
        world, world_summary = self._build_cognitive_world()
        predicted_set: set[str] = set()
        predicted_strength: dict[str, float] = {}

        if world is not None:
            for file_path in changed:
                consequences = world.predict_consequence(f"file:{file_path}")
                for effect, strength in consequences:
                    effect_str = str(effect)
                    if not effect_str.startswith("file:"):
                        continue
                    predicted = effect_str.split("file:", 1)[1]
                    if predicted not in indexed_files:
                        continue
                    predicted_set.add(predicted)
                    predicted_strength[predicted] = max(
                        float(strength), predicted_strength.get(predicted, 0.0)
                    )
                    if predicted not in distance or distance[predicted] > 1:
                        distance[predicted] = 1

        impacted = []
        for file_path, dist in sorted(distance.items(), key=lambda x: (x[1], x[0])):
            if dist == 0:
                kind = "changed"
                confidence = 1.0
            elif dist == 1:
                kind = "direct"
                confidence = 0.85
            else:
                kind = "transitive"
                confidence = max(0.25, round(0.75 / dist, 3))

            source = "graph"
            if dist == 0:
                source = "changed"
            elif file_path in static_distance and file_path in predicted_set:
                source = "graph+world_model"
            elif file_path in predicted_set and file_path not in static_distance:
                source = "world_model"
                confidence = max(confidence, round(predicted_strength.get(file_path, 0.4), 3))
            elif file_path in predicted_set:
                confidence = max(confidence, round(predicted_strength.get(file_path, confidence), 3))

            impacted.append(
                {
                    "file_path": file_path,
                    "distance": dist,
                    "impact_kind": kind,
                    "confidence": confidence,
                    "impact_source": source,
                }
            )

        direct_count = sum(1 for item in impacted if item["impact_kind"] == "direct")
        transitive_count = sum(1 for item in impacted if item["impact_kind"] == "transitive")
        return {
            "changed_files": changed,
            "impacted": impacted,
            "direct_count": direct_count,
            "transitive_count": transitive_count,
            "world_model": world_summary,
            "world_predicted_files": sorted(predicted_set),
            "max_depth": max_depth,
        }

    def index_stats(self) -> dict[str, int]:
        """Return persistent index counters."""
        return self.store.get_counts()
