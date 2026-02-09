"""Runtime composition entry points."""

from cross_module_engine.runtime.bootstrap import build_default_runtime
from cross_module_engine.runtime.registry import default_processors

__all__ = ["build_default_runtime", "default_processors"]


