from workflow_engine.contracts.processor import Processor
from workflow_engine.contracts.work_item import WorkItem
from workflow_engine.models.run_result import RunResult
from workflow_engine.processors.base_processor import BaseProcessor


class PushProcessor(BaseProcessor):
    """Push notification processor."""

    @property
    def name(self) -> str:
        return "push"

    def _deliver(self, item: WorkItem) -> str:
        # Simulate push delivery
        return "push_sent"
