"""Abstract contract for delivery policies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from layered_engine.contracts.work_item import WorkItem


class PolicyRule(ABC):
    """Evaluates whether a work item is allowed for processing."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Policy identifier."""

    @abstractmethod
    def allows(self, item: WorkItem) -> bool:
        """Return True when the item passes policy checks."""

