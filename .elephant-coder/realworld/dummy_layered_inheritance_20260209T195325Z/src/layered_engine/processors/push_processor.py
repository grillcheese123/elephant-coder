"""Push notification processor with policy enforcement."""

from __future__ import annotations

from layered_engine.contracts.processor import Processor
from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.policies.basic_rules import AllowAllRule
from layered_engine.processors.auditable_mixin import AuditableMixin
from layered_engine.processors.guarded_processor import GuardedProcessor


class PushProcessor(AuditableMixin, GuardedProcessor):
    """Processes push notification work items."""

    def __init__(self) -> None:
        """Initialize push processor with allow-all policy."""
        super().__init__()
        self._policy = AllowAllRule("push_policy")

    @property
    def name(self) -> str:
        """Return processor name."""
        return "push"

    def supports(self, item: WorkItem) -> bool:
        """Check if item is supported (push channel)."""
        return item.channel == "push"

    def deliver(self, item: WorkItem) -> RunResult:
        """Deliver push notification."""
        try:
            # Simulate push delivery
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=True,
                details="Push notification delivered successfully"
            )
        except Exception as e:
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=False,
                details=str(e)
            )
