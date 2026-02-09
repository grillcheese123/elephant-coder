"""Abstract processor contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from workflow_engine.contracts.work_item import WorkItem
from workflow_engine.models.run_result import RunResult


class Processor(ABC):
    """Processes work items for a supported channel."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable processor name."""

    @abstractmethod
    def supports(self, item: WorkItem) -> bool:
        """Whether this processor can handle the given item."""

    @abstractmethod
    def process(self, item: WorkItem) -> RunResult:
        """Process one work item and return a result object."""

