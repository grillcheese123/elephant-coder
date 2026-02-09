"""Email processor implementation."""

from __future__ import annotations

from event_mesh.contracts.work_item import WorkItem
from event_mesh.processors.base_processor import BaseProcessor


class EmailProcessor(BaseProcessor):
    supported_channel = "email"

    def _deliver(self, item: WorkItem) -> str:
        to_address = item.payload.get("to", "unknown")
        subject = item.payload.get("subject", "no-subject")
        return f"email delivered to {to_address} with subject {subject}"


