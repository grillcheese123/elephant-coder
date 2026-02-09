"""Runtime processor registry."""

from layered_engine.contracts.processor import Processor
from layered_engine.processors.push_processor import PushProcessor
from layered_engine.processors.prioritized_processor import PrioritizedProcessor


class ProcessorRegistry:
    """Registry for available processors."""

    def __init__(self) -> None:
        """Initialize registry with default processors."""
        self._processors: list[Processor] = [
            PrioritizedProcessor(),
            PushProcessor(),
        ]

    def get_processors(self) -> list[Processor]:
        """Return all registered processors."""
        return self._processors.copy()

    def find_processor(self, item_channel: str) -> Processor | None:
        """Find processor supporting given channel."""
        for processor in self._processors:
            if processor.supports(item_channel):
                return processor
        return None
