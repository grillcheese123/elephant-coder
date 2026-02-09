"""SMS processor implementation."""

from __future__ import annotations

from event_mesh.contracts.work_item import WorkItem
from event_mesh.processors.base_processor import BaseProcessor


class SmsProcessor(BaseProcessor):
    supported_channel = "sms"

    def _deliver(self, item: WorkItem) -> str:
        phone = item.payload.get("phone", "unknown")
        return f"sms delivered to {phone}"


