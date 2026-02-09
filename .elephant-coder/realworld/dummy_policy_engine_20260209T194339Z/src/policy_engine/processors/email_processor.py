"""Email processor implementation."""

from __future__ import annotations

from policy_engine.contracts.work_item import WorkItem
from policy_engine.processors.base_processor import BaseProcessor


class EmailProcessor(BaseProcessor):
    supported_channel = "email"

    def _deliver(self, item: WorkItem) -> str:
        to_address = item.payload.get("to", "unknown")
        subject = item.payload.get("subject", "no-subject")
        return f"email delivered to {to_address} with subject {subject}"


