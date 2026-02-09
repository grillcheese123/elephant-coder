"""Concrete work item model."""

from __future__ import annotations

from dataclasses import dataclass

from policy_engine.contracts.work_item import WorkItem


@dataclass(frozen=True)
class Ticket(WorkItem):
    """Concrete work item used by processors."""

    ticket_id: str
    target_channel: str
    data: dict[str, str]

    @property
    def identifier(self) -> str:
        return self.ticket_id

    @property
    def channel(self) -> str:
        return self.target_channel

    @property
    def payload(self) -> dict[str, str]:
        return self.data


