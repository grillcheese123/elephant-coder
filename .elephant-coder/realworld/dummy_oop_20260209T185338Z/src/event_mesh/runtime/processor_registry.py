"""Runtime processor registry."""

from __future__ import annotations

from event_mesh.contracts.processor import Processor
from event_mesh.contracts.work_item import WorkItem
from event_mesh.models.push_ticket import PushTicket
from event_mesh.models.ticket import Ticket
from event_mesh.processors.push_processor import PushProcessor


class ProcessorRegistry:
    """Registry of available processors."""

    def __init__(self) -> None:
        self._processors: list[Processor] = []
        self._register_default_processors()

    def _register_default_processors(self) -> None:
        self._processors.append(PushProcessor())

    def register(self, processor: Processor) -> None:
        """Register a new processor."""
        self._processors.append(processor)

    def get_processor(self, item: WorkItem) -> Processor | None:
        """Find a processor that supports the given item."""
        for processor in self._processors:
            if processor.supports(item):
                return processor
        return None
