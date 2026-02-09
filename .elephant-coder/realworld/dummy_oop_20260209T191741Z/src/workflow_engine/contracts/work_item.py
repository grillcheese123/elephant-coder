"""Abstract work item contract."""

from __future__ import annotations

from abc import ABC, abstractmethod


class WorkItem(ABC):
    """Unit of work dispatched through the system."""

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Stable identifier for traceability."""

    @property
    @abstractmethod
    def channel(self) -> str:
        """Delivery channel, for example email or sms."""

    @property
    @abstractmethod
    def payload(self) -> dict[str, str]:
        """Message payload."""

