"""Runtime bootstrap for app entry points."""

from __future__ import annotations

from cross_module_engine.contracts.repository import WorkItemRepository
from cross_module_engine.repositories.in_memory_repository import InMemoryWorkItemRepository
from cross_module_engine.runtime.registry import default_processors
from cross_module_engine.services.dispatcher import DispatcherService


def build_default_runtime() -> tuple[DispatcherService, WorkItemRepository]:
    """Build dispatcher + repository pair using default components."""
    repository = InMemoryWorkItemRepository()
    dispatcher = DispatcherService(repository, default_processors())
    return dispatcher, repository


