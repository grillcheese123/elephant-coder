"""Runtime processor registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from event_mesh.contracts.processor import Processor

from event_mesh.processors.email_processor import EmailProcessor
from event_mesh.processors.push_processor import PushProcessor
from event_mesh.processors.sms_processor import SmsProcessor


def get_processors() -> list[Processor]:
    """Return all registered processors."""
    return [
        EmailProcessor(),
        PushProcessor(),
        SmsProcessor(),
    ]
