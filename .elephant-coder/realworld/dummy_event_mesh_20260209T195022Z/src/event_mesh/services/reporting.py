"""Read-side reporting helpers."""

from __future__ import annotations

from event_mesh.contracts.repository import WorkItemRepository


def summarize_channels(repository: WorkItemRepository) -> dict[str, int]:
    """Return counts of items by channel."""
    summary: dict[str, int] = {}
    for item in repository.list_all():
        summary[item.channel] = summary.get(item.channel, 0) + 1
    return summary


