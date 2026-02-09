"""Webhook processor implementation."""

from __future__ import annotations

from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.processors.reliable_processor import ReliableProcessor


class WebhookProcessor(ReliableProcessor):
    supported_channel = "webhook"
    retries = 2

    def render_message(self, item: WorkItem) -> str:
        endpoint = item.payload.get("url", "unknown")
        return f"webhook delivered to {endpoint}"


