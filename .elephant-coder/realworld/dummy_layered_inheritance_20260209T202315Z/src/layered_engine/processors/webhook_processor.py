"""Webhook processor implementation."""

from __future__ import annotations

from layered_engine.contracts.policy_rule import PolicyRule
from layered_engine.contracts.work_item import WorkItem
from layered_engine.policies.basic_rules import RequiredPayloadKeysRule
from layered_engine.processors.prioritized_processor import PrioritizedProcessor


class WebhookProcessor(PrioritizedProcessor):
    supported_channel = "webhook"
    priority = 30

    @property
    def policy(self) -> PolicyRule:
        return RequiredPayloadKeysRule(
            name="webhook_payload_keys",
            required_keys=["url"],
        )

    def _deliver(self, item: WorkItem) -> str:
        endpoint = item.payload.get("url", "unknown")
        return f"webhook delivered to {endpoint}"


