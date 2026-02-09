"""Webhook processor implementation."""

from __future__ import annotations

from policy_engine.contracts.work_item import WorkItem
from policy_engine.processors.base_processor import BaseProcessor


class WebhookProcessor(BaseProcessor):
    supported_channel = "webhook"

    def _deliver(self, item: WorkItem) -> str:
        endpoint = item.payload.get("url", "unknown")
        return f"webhook delivered to {endpoint}"


