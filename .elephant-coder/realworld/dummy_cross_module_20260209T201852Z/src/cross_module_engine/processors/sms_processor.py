"""SMS processor implementation."""

from __future__ import annotations

from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.processors.reliable_processor import ReliableProcessor


class SmsProcessor(ReliableProcessor):
    supported_channel = "sms"
    retries = 3

    def render_message(self, item: WorkItem) -> str:
        phone = item.payload.get("phone", "unknown")
        return f"sms delivered to {phone}"


