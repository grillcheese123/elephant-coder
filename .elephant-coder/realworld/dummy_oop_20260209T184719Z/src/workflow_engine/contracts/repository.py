"""Abstract repository contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from workflow_engine.contracts.work_item import WorkItem


class WorkItemRepository(ABC):
    """Persistence boundary for work items."""

    @abstractmethod
    def save(self, item: WorkItem) -> None:
        """Persist one item."""

    @abstractmethod
    def get(self, identifier: str) -> WorkItem | None:
        """Read one item by id."""

    @abstractmethod
    def list_by_channel(self, channel: str) -> list[WorkItem]:
        """List items that target a specific channel."""

    @abstractmethod
    def list_all(self) -> list[WorkItem]:
        """List all stored items."""

