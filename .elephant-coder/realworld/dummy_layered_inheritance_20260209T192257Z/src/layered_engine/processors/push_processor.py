"""Push notification processor with policy enforcement."""

from __future__ import annotations

from layered_engine.contracts.processor import Processor
from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.policies.basic_rules import RequiredPayloadKeysRule
from layered_engine.processors.auditable_mixin import AuditableMixin
from layered_engine.processors.guarded_processor import GuardedProcessor


class PushProcessor(GuardedProcessor, AuditableMixin):
    """Processes push notification work items."""

    def __init__(self) -> None:
        """Initialize push processor with required payload keys policy."""
        GuardedProcessor.__init__(self)
        self._policy = RequiredPayloadKeysRule("push_payload", ["title", "message", "token"])

    @property
    def name(self) -> str:
        """Return processor name."""
        return "push"

    def supports(self, item: WorkItem) -> bool:
        """Check if item is for push channel."""
        return item.channel == "push"

    def deliver(self, item: WorkItem) -> RunResult:
        """Deliver push notification."""
        try:
            title = item.payload.get("title", "")
            message = item.payload.get("message", "")
            token = item.payload.get("token", "")
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=True,
                details=f"Push sent to {token}: [{title}] {message}"
            )
        except Exception as e:
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=False,
                details=str(e)
            )
