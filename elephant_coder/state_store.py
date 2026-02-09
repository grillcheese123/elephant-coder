"""SQLite-backed state store for Elephant Coder."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class StateStore:
    """Persist indexed files, symbols, dependencies, and graph edges."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS indexed_files (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                mtime REAL NOT NULL,
                indexed_at REAL NOT NULL,
                parse_error TEXT
            );

            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                symbol_name TEXT NOT NULL,
                qualname TEXT NOT NULL,
                kind TEXT NOT NULL,
                lineno INTEGER NOT NULL,
                end_lineno INTEGER NOT NULL,
                signature TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                module_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                caller_qualname TEXT NOT NULL,
                callee_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                src_file TEXT NOT NULL,
                dst_file TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                weight REAL NOT NULL DEFAULT 1.0,
                UNIQUE(src_file, dst_file, edge_type)
            );

            CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path);
            CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(symbol_name);
            CREATE INDEX IF NOT EXISTS idx_imports_file ON imports(file_path);
            CREATE INDEX IF NOT EXISTS idx_calls_file ON calls(file_path);
            CREATE INDEX IF NOT EXISTS idx_calls_callee ON calls(callee_name);
            CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_file);
            CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_file);
            """
        )
        self._conn.commit()

    def get_indexed_file_meta(self) -> dict[str, dict[str, Any]]:
        """Return indexed file metadata keyed by file path."""
        rows = self._conn.execute(
            "SELECT file_path, file_hash, mtime, parse_error FROM indexed_files"
        ).fetchall()
        return {
            row["file_path"]: {
                "file_hash": row["file_hash"],
                "mtime": float(row["mtime"]),
                "parse_error": row["parse_error"],
            }
            for row in rows
        }

    def upsert_indexed_file(
        self,
        file_path: str,
        file_hash: str,
        mtime: float,
        indexed_at: float,
        parse_error: str | None,
    ) -> None:
        """Insert or update indexed file metadata."""
        self._conn.execute(
            """
            INSERT INTO indexed_files (file_path, file_hash, mtime, indexed_at, parse_error)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                file_hash = excluded.file_hash,
                mtime = excluded.mtime,
                indexed_at = excluded.indexed_at,
                parse_error = excluded.parse_error
            """,
            (file_path, file_hash, mtime, indexed_at, parse_error),
        )
        self._conn.commit()

    def delete_file(self, file_path: str) -> None:
        """Delete all records related to one file."""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM indexed_files WHERE file_path = ?", (file_path,))
        cur.execute("DELETE FROM symbols WHERE file_path = ?", (file_path,))
        cur.execute("DELETE FROM imports WHERE file_path = ?", (file_path,))
        cur.execute("DELETE FROM calls WHERE file_path = ?", (file_path,))
        cur.execute("DELETE FROM edges WHERE src_file = ? OR dst_file = ?", (file_path, file_path))
        self._conn.commit()

    def replace_file_analysis(
        self,
        file_path: str,
        symbols: list[dict[str, Any]],
        imports: list[str],
        calls: list[dict[str, str]],
    ) -> None:
        """Replace symbols/imports/calls for a single file."""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM symbols WHERE file_path = ?", (file_path,))
        cur.execute("DELETE FROM imports WHERE file_path = ?", (file_path,))
        cur.execute("DELETE FROM calls WHERE file_path = ?", (file_path,))

        if symbols:
            cur.executemany(
                """
                INSERT INTO symbols
                    (file_path, symbol_name, qualname, kind, lineno, end_lineno, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        file_path,
                        str(item["symbol_name"]),
                        str(item["qualname"]),
                        str(item["kind"]),
                        int(item["lineno"]),
                        int(item["end_lineno"]),
                        str(item.get("signature", "")),
                    )
                    for item in symbols
                ],
            )

        if imports:
            cur.executemany(
                "INSERT INTO imports (file_path, module_name) VALUES (?, ?)",
                [(file_path, str(module)) for module in imports],
            )

        if calls:
            cur.executemany(
                "INSERT INTO calls (file_path, caller_qualname, callee_name) VALUES (?, ?, ?)",
                [
                    (file_path, str(item["caller_qualname"]), str(item["callee_name"]))
                    for item in calls
                ],
            )

        self._conn.commit()

    def list_imports(self) -> list[dict[str, Any]]:
        """Return all import rows."""
        rows = self._conn.execute("SELECT file_path, module_name FROM imports").fetchall()
        return [dict(row) for row in rows]

    def list_calls(self) -> list[dict[str, Any]]:
        """Return all call rows."""
        rows = self._conn.execute(
            "SELECT file_path, caller_qualname, callee_name FROM calls"
        ).fetchall()
        return [dict(row) for row in rows]

    def list_symbols(self) -> list[dict[str, Any]]:
        """Return all symbol rows."""
        rows = self._conn.execute(
            """
            SELECT file_path, symbol_name, qualname, kind, lineno, end_lineno, signature
            FROM symbols
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def symbol_files_by_name(self) -> dict[str, set[str]]:
        """Map symbol names to files where they are defined."""
        rows = self._conn.execute("SELECT symbol_name, file_path FROM symbols").fetchall()
        out: dict[str, set[str]] = {}
        for row in rows:
            out.setdefault(str(row["symbol_name"]), set()).add(str(row["file_path"]))
        return out

    def replace_edges(self, edges: list[dict[str, Any]]) -> None:
        """Replace complete edge set."""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM edges")
        if edges:
            cur.executemany(
                """
                INSERT OR IGNORE INTO edges (src_file, dst_file, edge_type, weight)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        str(item["src_file"]),
                        str(item["dst_file"]),
                        str(item["edge_type"]),
                        float(item.get("weight", 1.0)),
                    )
                    for item in edges
                ],
            )
        self._conn.commit()

    def list_edges(self) -> list[dict[str, Any]]:
        """Return all graph edges."""
        rows = self._conn.execute(
            "SELECT src_file, dst_file, edge_type, weight FROM edges"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_counts(self) -> dict[str, int]:
        """Return key record counts."""
        table_names = ("indexed_files", "symbols", "imports", "calls", "edges")
        counts: dict[str, int] = {}
        for table in table_names:
            counts[table] = int(
                self._conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
            )
        counts["parse_errors"] = int(
            self._conn.execute(
                "SELECT COUNT(*) AS c FROM indexed_files WHERE parse_error IS NOT NULL"
            ).fetchone()["c"]
        )
        return counts

    def close(self) -> None:
        """Close DB connection."""
        self._conn.close()
