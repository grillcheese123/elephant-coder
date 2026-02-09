"""Processor run result model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunResult:
    """Represents one processing attempt."""

    processor: str
    item_id: str
    success: bool
    details: str

