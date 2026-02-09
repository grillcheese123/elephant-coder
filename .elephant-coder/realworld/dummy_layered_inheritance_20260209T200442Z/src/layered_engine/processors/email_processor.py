"""Email processor implementation."""

from __future__ import annotations

from layered_engine.contracts.policy_rule import PolicyRule
from layered_engine.contracts.work_item import WorkItem
from layered_engine.policies.basic_rules import RequiredPayloadKeysRule
from layered_engine.processors.prioritized_processor import PrioritizedProcessor


class EmailProcessor(PrioritizedProcessor):
    supported_channel = "email"
    priority = 10

    @property
    def policy(self) -> PolicyRule:
        return RequiredPayloadKeysRule(
            name="email_payload_keys",
            required_keys=["to", "subject"],
        )

    def _deliver(self, item: WorkItem) -> str:
        to_address = item.payload.get("to", "unknown")
        subject = item.payload.get("subject", "no-subject")
        return f"email delivered to {to_address} with subject {subject}"


