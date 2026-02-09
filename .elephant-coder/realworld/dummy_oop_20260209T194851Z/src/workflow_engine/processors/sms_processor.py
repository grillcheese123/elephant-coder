"""SMS processor implementation."""

from __future__ import annotations

from workflow_engine.contracts.work_item import WorkItem
from workflow_engine.processors.base_processor import BaseProcessor


class SmsProcessor(BaseProcessor):
    supported_channel = "sms"

    def _deliver(self, item: WorkItem) -> str:
        phone = item.payload.get("phone", "unknown")
        return f"sms delivered to {phone}"

