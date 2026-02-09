"""Push notification processor implementation."""

from __future__ import annotations

from cross_module_engine.channels.delivery_adapter import DeliveryAdapter
from cross_module_engine.contracts.processor import Processor
from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult
from cross_module_engine.processors.channel_bound_processor import ChannelBoundProcessor


class PushProcessor(ChannelBoundProcessor):
    """Processor for push notification delivery."""

    @property
    def name(self) -> str:
        return "push"

    def supports(self, item: WorkItem) -> bool:
        return item.channel == "push"

    @property
    def adapter(self) -> DeliveryAdapter:
        return DeliveryAdapter("push")
