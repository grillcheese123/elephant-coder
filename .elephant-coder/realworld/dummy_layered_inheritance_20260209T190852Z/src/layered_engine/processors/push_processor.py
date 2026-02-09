from __future__ import annotations

from layered_engine.contracts.processor import Processor
from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.policies.basic_rules import AllowAllRule
from layered_engine.processors.auditable_mixin import AuditableMixin
from layered_engine.processors.guarded_processor import GuardedProcessor


class PushProcessor(GuardedProcessor, AuditableMixin):
    """Processor for push notification delivery."""

    def __init__(self) -> None:
        super().__init__(AllowAllRule())

    @property
    def name(self) -> str:
        return "push"

    def supports(self, item: WorkItem) -> bool:
        return item.channel == "push"

    def deliver(self, item: WorkItem) -> bool:
        """Simulate push delivery."""
        return True

    def process(self, item: WorkItem) -> RunResult:
        if not self.supports(item):
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=False,
                details="Channel not supported",
            )

        if not self.policy.allows(item):
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=False,
                details="Policy not allowed",
            )

        success = self.deliver(item)
        return RunResult(
            processor=self.name,
            item_id=item.identifier,
            success=success,
            details="Push delivered" if success else "Push failed",
        )
