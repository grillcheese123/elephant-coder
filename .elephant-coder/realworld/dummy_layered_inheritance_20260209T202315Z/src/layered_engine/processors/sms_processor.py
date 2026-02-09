"""SMS processor implementation."""

from __future__ import annotations

from layered_engine.contracts.policy_rule import PolicyRule
from layered_engine.contracts.work_item import WorkItem
from layered_engine.policies.basic_rules import RequiredPayloadKeysRule
from layered_engine.processors.prioritized_processor import PrioritizedProcessor


class SmsProcessor(PrioritizedProcessor):
    supported_channel = "sms"
    priority = 20

    @property
    def policy(self) -> PolicyRule:
        return RequiredPayloadKeysRule(
            name="sms_payload_keys",
            required_keys=["phone"],
        )

    def _deliver(self, item: WorkItem) -> str:
        phone = item.payload.get("phone", "unknown")
        return f"sms delivered to {phone}"


