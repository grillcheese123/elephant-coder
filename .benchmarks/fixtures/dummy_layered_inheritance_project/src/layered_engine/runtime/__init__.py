"""Runtime composition entry points."""

from layered_engine.runtime.bootstrap import build_default_runtime
from layered_engine.runtime.registry import default_processors

__all__ = ["build_default_runtime", "default_processors"]


