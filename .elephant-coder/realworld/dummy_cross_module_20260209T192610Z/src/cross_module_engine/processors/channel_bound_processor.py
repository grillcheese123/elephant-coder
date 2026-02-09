"""Processor layer that binds delivery interface implementations."""

from __future__ import annotations

from abc import abstractmethod

from cross_module_engine.channels.delivery_adapter import DeliveryAdapter
from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.interfaces.delivery_interface import DeliveryInterface
from cross_module_engine.processors.base_processor import BaseProcessor


class ChannelBoundProcessor(BaseProcessor):
    """Base processor layer that delegates emit to a delivery interface."""

    adapter_cls = DeliveryAdapter

    def __init__(self):
        self._adapter: DeliveryInterface = self.adapter_cls(self.supported_channel)

    @property
    def adapter(self) -> DeliveryInterface:
        return self._adapter

    @abstractmethod
    def render_message(self, item: WorkItem) -> str:
        """Render item payload into channel-specific message text."""

    def _deliver(self, item: WorkItem) -> str:
        return self.adapter.emit(self.render_message(item))

