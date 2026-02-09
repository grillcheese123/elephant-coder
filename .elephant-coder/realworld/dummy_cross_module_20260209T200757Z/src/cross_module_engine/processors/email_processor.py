"""Email processor implementation."""

from __future__ import annotations

from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.processors.reliable_processor import ReliableProcessor


class EmailProcessor(ReliableProcessor):
    supported_channel = "email"
    retries = 1

    def render_message(self, item: WorkItem) -> str:
        to_address = item.payload.get("to", "unknown")
        subject = item.payload.get("subject", "no-subject")
        return f"email delivered to {to_address} with subject {subject}"


