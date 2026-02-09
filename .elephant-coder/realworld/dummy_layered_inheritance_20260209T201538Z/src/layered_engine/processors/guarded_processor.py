"""Policy-guarded processor base class."""

from __future__ import annotations

from abc import abstractmethod

from layered_engine.contracts.policy_rule import PolicyRule
from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.processors.base_processor import BaseProcessor


class GuardedProcessor(BaseProcessor):
    """Adds rule checks before delivery."""

    @property
    @abstractmethod
    def policy(self) -> PolicyRule:
        """Policy rule used by this processor."""

    def process(self, item: WorkItem) -> RunResult:
        if not self.supports(item):
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=False,
                details=f"unsupported channel: {item.channel}",
            )
        if not self.policy.allows(item):
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=False,
                details=f"policy blocked by {self.policy.name}",
            )
        return super().process(item)

