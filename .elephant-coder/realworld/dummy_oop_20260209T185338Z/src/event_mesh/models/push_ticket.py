"""Concrete push notification work item model."""

from __future__ import annotations

from dataclasses import dataclass

from event_mesh.contracts.work_item import WorkItem


@dataclass(frozen=True)
class PushTicket(WorkItem):
    """Concrete work item for push notifications."""

    ticket_id: str
    target_channel: str
    data: dict[str, str]
    device_token: str

    @property
    def identifier(self) -> str:
        return self.ticket_id

    @property
    def channel(self) -> str:
        return self.target_channel

    @property
    def payload(self) -> dict[str, str]:
        return self.data
