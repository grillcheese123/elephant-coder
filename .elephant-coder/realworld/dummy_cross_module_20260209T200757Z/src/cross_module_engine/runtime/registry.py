"""Runtime processor registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cross_module_engine.contracts.processor import Processor

from cross_module_engine.processors.push_processor import PushProcessor
from cross_module_engine.processors.reliable_processor import ReliableProcessor


def get_processors() -> list[Processor]:
    """Return registered processors."""
    return [
        ReliableProcessor(),
        PushProcessor(),
    ]
