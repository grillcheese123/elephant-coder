"""Runtime processor registry."""

from cross_module_engine.contracts.processor import Processor
from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.processors.push_processor import PushProcessor
from cross_module_engine.processors.reliable_processor import ReliableProcessor


class ProcessorRegistry:
    """Registry of available processors."""

    def __init__(self) -> None:
        self._processors: list[Processor] = [
            PushProcessor(),
            ReliableProcessor(),
        ]

    def get_processor(self, item: WorkItem) -> Processor:
        """Get the first processor that supports the given item."""
        for processor in self._processors:
            if processor.supports(item):
                return processor
        raise ValueError(f"No processor supports item with channel '{item.channel}'")

    def list_all(self) -> list[Processor]:
        """List all registered processors."""
        return list(self._processors)
