"""Dispatcher service that routes work items to matching processors."""

from __future__ import annotations

from policy_engine.contracts.processor import Processor
from policy_engine.contracts.repository import WorkItemRepository
from policy_engine.contracts.work_item import WorkItem
from policy_engine.models.run_result import RunResult


class DispatcherService:
    """Coordinates processor selection and persistence."""

    def __init__(self, repository: WorkItemRepository, processors: list[Processor]):
        self.repository = repository
        self.processors = list(processors)

    def register_processor(self, processor: Processor) -> None:
        self.processors.append(processor)

    def dispatch(self, item: WorkItem) -> RunResult:
        self.repository.save(item)
        for processor in self.processors:
            if processor.supports(item):
                return processor.process(item)
        raise LookupError(f"No processor found for channel={item.channel}")


