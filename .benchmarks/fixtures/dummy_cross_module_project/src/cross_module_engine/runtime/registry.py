"""Default processor registry."""

from __future__ import annotations

from cross_module_engine.contracts.processor import Processor
from cross_module_engine.processors.email_processor import EmailProcessor
from cross_module_engine.processors.sms_processor import SmsProcessor
from cross_module_engine.processors.webhook_processor import WebhookProcessor


def default_processors() -> list[Processor]:
    """Instantiate the default processor set."""
    return [
        EmailProcessor(),
        SmsProcessor(),
        WebhookProcessor(),
    ]


