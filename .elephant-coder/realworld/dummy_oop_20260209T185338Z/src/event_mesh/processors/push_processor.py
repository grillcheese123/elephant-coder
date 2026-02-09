"""Push notification processor."""

from __future__ import annotations

from event_mesh.contracts.processor import Processor
from event_mesh.contracts.work_item import WorkItem
from event_mesh.models.push_ticket import PushTicket
from event_mesh.models.run_result import RunResult


class PushProcessor(Processor):
    """Processes push notification work items."""

    @property
    def name(self) -> str:
        return "push"

    def supports(self, item: WorkItem) -> bool:
        return isinstance(item, PushTicket)

    def process(self, item: WorkItem) -> RunResult:
        if not self.supports(item):
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=False,
                details="Unsupported work item type"
            )

        # Simulate push dispatch
        return RunResult(
            processor=self.name,
            item_id=item.identifier,
            success=True,
            details=f"Push dispatched to device {getattr(item, 'device_token', 'unknown')}"
        )
