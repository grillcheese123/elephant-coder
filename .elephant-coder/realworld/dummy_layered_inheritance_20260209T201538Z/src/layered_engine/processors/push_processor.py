"""Push notification processor with policy enforcement."""

from __future__ import annotations

from layered_engine.contracts.policy_rule import PolicyRule
from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.policies.basic_rules import AllowAllRule
from layered_engine.processors.auditable_mixin import AuditableMixin
from layered_engine.processors.guarded_processor import GuardedProcessor


class PushProcessor(GuardedProcessor, AuditableMixin):
    """Processes push notification work items."""

    def __init__(self) -> None:
        """Initialize the push processor with default policy."""
        super().__init__()
        self._policy: PolicyRule = AllowAllRule()

    @property
    def name(self) -> str:
        """Return processor name."""
        return "push"

    def supports(self, item: WorkItem) -> bool:
        """Check if item is supported (push channel)."""
        return item.channel == "push"

    def deliver(self, item: WorkItem) -> bool:
        """Simulate push delivery."""
        return True

    def _process_impl(self, item: WorkItem) -> RunResult:
        """Execute push delivery with audit support."""
        success = self.deliver(item)
        return RunResult(
            processor=self.name,
            item_id=item.identifier,
            success=success,
            details="Push notification delivered successfully" if success else "Push notification failed"
        )
