"""Push notification work item repository."""

from __future__ import annotations

from policy_engine.contracts.repository import WorkItemRepository
from policy_engine.contracts.work_item import WorkItem
from policy_engine.models.push_ticket import PushTicket


class PushRepository(WorkItemRepository):
    """In-memory repository for push notification work items."""

    def __init__(self) -> None:
        self._items: dict[str, WorkItem] = {}

    def save(self, item: WorkItem) -> None:
        self._items[item.identifier] = item

    def get(self, identifier: str) -> WorkItem | None:
        return self._items.get(identifier)

    def list_by_channel(self, channel: str) -> list[WorkItem]:
        return [item for item in self._items.values() if item.channel == channel]

    def list_all(self) -> list[WorkItem]:
        return list(self._items.values())
