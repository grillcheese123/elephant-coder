"""Default processor registry."""

from __future__ import annotations

from event_mesh.contracts.processor import Processor
from event_mesh.processors.email_processor import EmailProcessor
from event_mesh.processors.sms_processor import SmsProcessor
from event_mesh.processors.webhook_processor import WebhookProcessor


def default_processors() -> list[Processor]:
    """Instantiate the default processor set."""
    return [
        EmailProcessor(),
        SmsProcessor(),
        WebhookProcessor(),
    ]


