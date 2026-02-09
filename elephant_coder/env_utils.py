"""Environment file utilities."""

from __future__ import annotations

from pathlib import Path


def load_dotenv(project_root: Path, filename: str = ".env") -> int:
    """Load KEY=VALUE pairs from a dotenv file into process env.

    Existing environment variables are not overwritten.

    Returns:
        Number of keys loaded.
    """
    import os

    dotenv_path = project_root / filename
    if not dotenv_path.exists():
        return 0

    loaded = 0
    for raw_line in dotenv_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
            value = value[1:-1]
        if key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded
