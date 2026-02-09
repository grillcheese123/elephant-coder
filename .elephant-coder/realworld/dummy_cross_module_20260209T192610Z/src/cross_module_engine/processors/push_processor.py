"""Push notification processor implementation."""

from __future__ import annotations

from cross_module_engine.channels.delivery_adapter import DeliveryAdapter
from cross_module_engine.contracts.processor import Processor
from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult
from cross_module_engine.processors.channel_bound_processor import ChannelBoundProcessor


class PushProcessor(ChannelBoundProcessor):
    """Processor for push notifications."""

    @property
    def name(self) -> str:
        return "push"

    @property
    def adapter(self) -> DeliveryAdapter:
        return DeliveryAdapter("push")

    def process(self, item: WorkItem) -> RunResult:
        """Process push notification work item."""
        try:
            message = self.render_message(item)
            self._deliver(item)
            return RunResult.success(self.name, item.identifier, message)
        except Exception as e:
            return RunResult.failure(self.name, item.identifier, str(e))
