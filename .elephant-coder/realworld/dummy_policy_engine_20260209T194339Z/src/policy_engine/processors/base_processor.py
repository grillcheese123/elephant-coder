"""Shared processor base class."""

from __future__ import annotations

from abc import abstractmethod

from policy_engine.contracts.processor import Processor
from policy_engine.contracts.work_item import WorkItem
from policy_engine.models.run_result import RunResult


class BaseProcessor(Processor):
    """Default behavior for channel-specific processors."""

    supported_channel: str = ""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def supports(self, item: WorkItem) -> bool:
        return bool(self.supported_channel) and item.channel == self.supported_channel

    def process(self, item: WorkItem) -> RunResult:
        if not self.supports(item):
            return RunResult(
                processor=self.name,
                item_id=item.identifier,
                success=False,
                details=f"unsupported channel: {item.channel}",
            )
        details = self._deliver(item)
        return RunResult(
            processor=self.name,
            item_id=item.identifier,
            success=True,
            details=details,
        )

    @abstractmethod
    def _deliver(self, item: WorkItem) -> str:
        """Channel-specific side effect."""


