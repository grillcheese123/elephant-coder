"""Delivery interface shared across channel adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod


class DeliveryInterface(ABC):
    """Contract used by processors to emit channel messages."""

    @property
    @abstractmethod
    def channel(self) -> str:
        """Channel identifier."""

    @abstractmethod
    def emit(self, message: str) -> str:
        """Emit one already-rendered message."""

