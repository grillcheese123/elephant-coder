"""Runtime bootstrap for app entry points."""

from __future__ import annotations

from event_mesh.contracts.repository import WorkItemRepository
from event_mesh.repositories.in_memory_repository import InMemoryWorkItemRepository
from event_mesh.runtime.registry import default_processors
from event_mesh.services.dispatcher import DispatcherService


def build_default_runtime() -> tuple[DispatcherService, WorkItemRepository]:
    """Build dispatcher + repository pair using default components."""
    repository = InMemoryWorkItemRepository()
    dispatcher = DispatcherService(repository, default_processors())
    return dispatcher, repository


