from __future__ import annotations

from layered_engine.contracts.policy_rule import PolicyRule
from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.policies.basic_rules import AllowAllRule
from layered_engine.processors.auditable_mixin import AuditableMixin
from layered_engine.processors.guarded_processor import GuardedProcessor


class PushProcessor(GuardedProcessor, AuditableMixin):
    """Processor for push notification delivery."""

    def __init__(self) -> None:
        super().__init__()
        self._policy: PolicyRule = AllowAllRule()

    @property
    def name(self) -> str:
        return "push"

    @property
    def policy(self) -> PolicyRule:
        return self._policy

    def supports(self, item: WorkItem) -> bool:
        return item.channel == "push"

    def deliver(self, item: WorkItem) -> bool:
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
                details="Policy denied",
            )

        success = self.deliver(item)
        return RunResult(
            processor=self.name,
            item_id=item.identifier,
            success=success,
            details="Push delivered" if success else "Push failed",
        )
