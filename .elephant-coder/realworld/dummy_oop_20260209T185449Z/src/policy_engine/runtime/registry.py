"""Default processor registry."""

from __future__ import annotations

from policy_engine.contracts.processor import Processor
from policy_engine.processors.email_processor import EmailProcessor
from policy_engine.processors.sms_processor import SmsProcessor
from policy_engine.processors.webhook_processor import WebhookProcessor


def default_processors() -> list[Processor]:
    """Instantiate the default processor set."""
    return [
        EmailProcessor(),
        SmsProcessor(),
        WebhookProcessor(),
    ]


