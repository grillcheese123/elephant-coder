"""In-memory repository implementation."""

from __future__ import annotations

from policy_engine.contracts.repository import WorkItemRepository
from policy_engine.contracts.work_item import WorkItem


class InMemoryWorkItemRepository(WorkItemRepository):
    """Simple in-memory persistence for benchmark scenarios."""

    def __init__(self):
        self._items: dict[str, WorkItem] = {}

    def save(self, item: WorkItem) -> None:
        self._items[item.identifier] = item

    def get(self, identifier: str) -> WorkItem | None:
        return self._items.get(identifier)

    def list_by_channel(self, channel: str) -> list[WorkItem]:
        return [item for item in self._items.values() if item.channel == channel]

    def list_all(self) -> list[WorkItem]:
        return list(self._items.values())


