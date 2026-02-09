"""Runtime composition entry points."""

from event_mesh.runtime.bootstrap import build_default_runtime
from event_mesh.runtime.registry import default_processors

__all__ = ["build_default_runtime", "default_processors"]


