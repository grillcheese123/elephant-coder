"""Runtime dispatcher for work items."""

from __future__ import annotations

from policy_engine.contracts.processor import Processor
from policy_engine.contracts.repository import WorkItemRepository
from policy_engine.contracts.work_item import WorkItem
from policy_engine.models.run_result import RunResult


class Dispatcher:
    """Dispatches work items to appropriate processors."""

    def __init__(
        self,
        processors: list[Processor],
        repository: WorkItemRepository,
    ) -> None:
        self._processors = processors
        self._repository = repository

    def dispatch(self, item: WorkItem) -> RunResult:
        """Dispatch one work item to the first supporting processor."""
        self._repository.save(item)
        for processor in self._processors:
            if processor.supports(item):
                return processor.process(item)
        return RunResult(
            processor="unknown",
            item_id=item.identifier,
            success=False,
            details="No processor supports this item",
        )
