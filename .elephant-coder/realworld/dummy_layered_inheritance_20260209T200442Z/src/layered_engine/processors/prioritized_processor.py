"""Priority-aware processor base class."""

from __future__ import annotations

from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.processors.auditable_mixin import AuditableMixin
from layered_engine.processors.guarded_processor import GuardedProcessor


class PrioritizedProcessor(GuardedProcessor, AuditableMixin):
    """Adds stable priority metadata to processing output."""

    priority: int = 100

    def process(self, item: WorkItem) -> RunResult:
        result = super().process(item)
        prefix = self.build_audit_prefix(
            processor=self.name,
            rule=self.policy.name,
            priority=int(self.priority),
        )
        return RunResult(
            processor=result.processor,
            item_id=result.item_id,
            success=result.success,
            details=f"{prefix} {result.details}",
        )

