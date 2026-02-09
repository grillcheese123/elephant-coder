from __future__ import annotations

from event_mesh.contracts.processor import Processor
from event_mesh.contracts.repository import WorkItemRepository
from event_mesh.contracts.work_item import WorkItem
from event_mesh.models.run_result import RunResult
from event_mesh.models.ticket import Ticket


class InMemoryRepository(WorkItemRepository):
    def __init__(self) -> None:
        self._items: dict[str, WorkItem] = {}

    def save(self, item: WorkItem) -> None:
        self._items[item.identifier] = item

    def get(self, identifier: str) -> WorkItem | None:
        return self._items.get(identifier)

    def list_by_channel(self, channel: str) -> list[WorkItem]:
        return [i for i in self._items.values() if i.channel == channel]

    def list_all(self) -> list[WorkItem]:
        return list(self._items.values())


class Runtime:
    def __init__(self, repository: WorkItemRepository, processors: list[Processor]) -> None:
        self.repository = repository
        self.processors = processors

    def dispatch(self, item: WorkItem) -> RunResult:
        self.repository.save(item)
        for proc in self.processors:
            if proc.supports(item):
                return proc.process(item)
        return RunResult(
            processor="unknown",
            item_id=item.identifier,
            success=False,
            details=f"no processor for channel {item.channel}",
        )


def build_default_runtime() -> Runtime:
    from event_mesh.processors.email_processor import EmailProcessor
    from event_mesh.processors.push_processor import PushProcessor

    repo = InMemoryRepository()
    processors: list[Processor] = [EmailProcessor()]
    try:
        processors.append(PushProcessor())
    except (ImportError, AttributeError):
        pass
    return Runtime(repo, processors)
