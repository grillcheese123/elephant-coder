"""Interface implementation used by processors."""

from __future__ import annotations

from cross_module_engine.channels.message_template import MessageTemplate
from cross_module_engine.interfaces.delivery_interface import DeliveryInterface


class DeliveryAdapter(DeliveryInterface):
    """Default delivery interface implementation."""

    def __init__(self, channel: str):
        self._channel = str(channel).strip()
        self._template = MessageTemplate(self._channel or "unknown")

    @property
    def channel(self) -> str:
        return self._channel

    def emit(self, message: str) -> str:
        return self._template.render(str(message))

