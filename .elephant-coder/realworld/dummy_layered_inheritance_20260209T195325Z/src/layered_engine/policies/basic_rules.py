"""Basic policy rules used by layered processors."""

from __future__ import annotations

from layered_engine.contracts.policy_rule import PolicyRule
from layered_engine.contracts.work_item import WorkItem


class AllowAllRule(PolicyRule):
    """Simple allow-all policy."""

    @property
    def name(self) -> str:
        return "allow_all"

    def allows(self, item: WorkItem) -> bool:
        return True


class RequiredPayloadKeysRule(PolicyRule):
    """Requires payload keys to be present and non-empty."""

    def __init__(self, name: str, required_keys: list[str]):
        self._name = str(name).strip() or "required_payload_keys"
        self.required_keys = [key for key in required_keys if str(key).strip()]

    @property
    def name(self) -> str:
        return self._name

    def allows(self, item: WorkItem) -> bool:
        for key in self.required_keys:
            if not item.payload.get(key):
                return False
        return True

