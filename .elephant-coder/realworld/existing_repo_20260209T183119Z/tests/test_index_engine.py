"""Tests for Elephant Coder incremental index and impact engine."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].resolve()
INDEX_MODULE_PATH = ROOT / "elephant_coder" / "index_engine.py"
STORE_MODULE_PATH = ROOT / "elephant_coder" / "state_store.py"


def _load_index_service():
    package_name = "elephant_coder"
    if package_name not in sys.modules:
        pkg_spec = importlib.util.spec_from_loader(package_name, loader=None)
        if pkg_spec is None:
            raise RuntimeError("Unable to create package spec for elephant_coder")
        pkg_module = importlib.util.module_from_spec(pkg_spec)
        pkg_module.__path__ = [str(ROOT / "elephant_coder")]  # type: ignore[attr-defined]
        sys.modules[package_name] = pkg_module

    store_name = "elephant_coder.state_store"
    if store_name not in sys.modules:
        store_spec = importlib.util.spec_from_file_location(store_name, STORE_MODULE_PATH)
        if store_spec is None or store_spec.loader is None:
            raise RuntimeError("Unable to load state_store.py")
        store_module = importlib.util.module_from_spec(store_spec)
        sys.modules[store_name] = store_module
        store_spec.loader.exec_module(store_module)

    index_name = "elephant_coder.index_engine"
    index_spec = importlib.util.spec_from_file_location(index_name, INDEX_MODULE_PATH)
    if index_spec is None or index_spec.loader is None:
        raise RuntimeError("Unable to load index_engine.py")
    index_module = importlib.util.module_from_spec(index_spec)
    sys.modules[index_name] = index_module
    index_spec.loader.exec_module(index_module)
    return index_module.IndexService


IndexService = _load_index_service()


def test_refresh_index_and_impact_propagation(tmp_path: Path):
    (tmp_path / "a.py").write_text("import b\n\nx = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    (tmp_path / "c.py").write_text("from b import foo\n\ndef bar():\n    return foo()\n", encoding="utf-8")

    svc = IndexService(tmp_path)
    try:
        stats = svc.refresh_index()
        assert stats["files_scanned"] == 3
        assert stats["symbols_total"] >= 2
        assert stats["edges_total"] >= 2

        impact = svc.impact_for_files(["b.py"])
        impacted_paths = [item["file_path"] for item in impact["impacted"]]
        assert "b.py" in impacted_paths
        assert "a.py" in impacted_paths
        assert "c.py" in impacted_paths
        assert impact["direct_count"] >= 2
        assert "world_model" in impact
        assert "enabled" in impact["world_model"]
    finally:
        svc.close()


def test_refresh_index_skips_unchanged_files(tmp_path: Path):
    (tmp_path / "m.py").write_text("def m():\n    return 1\n", encoding="utf-8")
    (tmp_path / "n.py").write_text("def n():\n    return 2\n", encoding="utf-8")

    svc = IndexService(tmp_path)
    try:
        first = svc.refresh_index()
        second = svc.refresh_index()
        assert first["files_indexed"] == 2
        assert second["files_indexed"] == 0
        assert second["files_skipped"] == 2
    finally:
        svc.close()


def test_parse_error_is_recorded(tmp_path: Path):
    (tmp_path / "ok.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text("def broken(:\n    return 0\n", encoding="utf-8")

    svc = IndexService(tmp_path)
    try:
        stats = svc.refresh_index()
        assert stats["parse_errors"] == 1
        counts = svc.index_stats()
        assert counts["parse_errors"] == 1
    finally:
        svc.close()


def test_world_model_reports_fact_counts(tmp_path: Path):
    (tmp_path / "x.py").write_text("import y\n\ndef x():\n    return y.v()\n", encoding="utf-8")
    (tmp_path / "y.py").write_text("def v():\n    return 3\n", encoding="utf-8")

    svc = IndexService(tmp_path)
    try:
        svc.refresh_index()
        impact = svc.impact_for_files(["y.py"])
        world = impact["world_model"]
        assert isinstance(world["enabled"], bool)
        assert "capsule_enabled" in world
        assert "capsule_active" in world
        assert "capsule_dim" in world
        assert "dim" in world
        if world["enabled"]:
            assert world["facts"] > 0
            assert world["edge_facts"] > 0
            assert world["capsule_active"] is True
    finally:
        svc.close()


def test_world_model_can_be_disabled_via_config_params(tmp_path: Path):
    (tmp_path / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")

    svc = IndexService(tmp_path, world_model_enabled=False)
    try:
        svc.refresh_index()
        impact = svc.impact_for_files(["a.py"])
        world = impact["world_model"]
        assert world["enabled"] is False
        assert world["error"] == "disabled by config"
        assert world["capsule_enabled"] is True
    finally:
        svc.close()


def test_world_model_reports_dimension_configuration(tmp_path: Path):
    (tmp_path / "m.py").write_text("import n\n\ndef m():\n    return n.v()\n", encoding="utf-8")
    (tmp_path / "n.py").write_text("def v():\n    return 2\n", encoding="utf-8")

    svc = IndexService(
        tmp_path,
        world_model_enabled=True,
        world_model_dim=640,
        world_model_capsule_dim=24,
        world_model_semantic_dims=20,
        world_model_max_edge_facts=1234,
        world_model_max_symbol_facts=222,
    )
    try:
        svc.refresh_index()
        impact = svc.impact_for_files(["n.py"])
        world = impact["world_model"]
        assert world["dim"] == 640
        assert world["capsule_dim"] == 24
        assert world["semantic_dims"] == 20
        assert world["max_edge_facts"] == 1234
        assert world["max_symbol_facts"] == 222
    finally:
        svc.close()
