"""Processor layer adding retry metadata."""

from __future__ import annotations

from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult
from cross_module_engine.processors.channel_bound_processor import ChannelBoundProcessor


class ReliableProcessor(ChannelBoundProcessor):
    """Adds reliability metadata to delivery output."""

    retries: int = 2

    def process(self, item: WorkItem) -> RunResult:
        result = super().process(item)
        return RunResult(
            processor=result.processor,
            item_id=result.item_id,
            success=result.success,
            details=f"[retries={self.retries}] {result.details}",
        )

