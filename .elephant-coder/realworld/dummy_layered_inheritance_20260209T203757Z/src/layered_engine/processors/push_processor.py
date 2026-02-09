"""Push notification processor with layered inheritance."""

from __future__ import annotations

from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.policies.basic_rules import AllowAllRule
from layered_engine.processors.guarded_processor import GuardedProcessor
from layered_engine.processors.prioritized_processor import PrioritizedProcessor


class PushProcessor(PrioritizedProcessor):
    """Processes push notification work items."""

    def __init__(self) -> None:
        super().__init__(policy=AllowAllRule())

    @property
    def name(self) -> str:
        return "push"

    def supports(self, item: WorkItem) -> bool:
        return item.channel == "push"

    def deliver(self, item: WorkItem) -> RunResult:
        """Deliver push notification."""
        return RunResult(
            processor=self.name,
            item_id=item.identifier,
            success=True,
            details="Push notification dispatched successfully",
        )
