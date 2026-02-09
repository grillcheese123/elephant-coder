"""Push notification processor implementation."""

from __future__ import annotations

from cross_module_engine.channels.delivery_adapter import DeliveryAdapter
from cross_module_engine.contracts.processor import Processor
from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult


class PushProcessor(Processor):
    """Processor for push notification delivery."""

    @property
    def name(self) -> str:
        return "push"

    def supports(self, item: WorkItem) -> bool:
        return item.channel == "push"

    def process(self, item: WorkItem) -> RunResult:
        try:
            adapter = self._get_adapter()
            message = self._render_message(item)
            adapter.emit(message)
            return RunResult.success(self.name, item.identifier)
        except Exception as e:
            return RunResult.failure(self.name, item.identifier, str(e))

    def _get_adapter(self) -> DeliveryAdapter:
        return DeliveryAdapter("push")

    def _render_message(self, item: WorkItem) -> str:
        return item.payload.get("message", "")
