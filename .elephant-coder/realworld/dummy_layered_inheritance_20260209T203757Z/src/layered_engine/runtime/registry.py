"""Runtime processor registry."""

from layered_engine.processors.email_processor import EmailProcessor
from layered_engine.processors.push_processor import PushProcessor
from layered_engine.processors.sms_processor import SmsProcessor
from layered_engine.processors.webhook_processor import WebhookProcessor


def get_processors() -> list:
    """Return list of available processors."""
    return [
        EmailProcessor(),
        SmsProcessor(),
        WebhookProcessor(),
        PushProcessor(),
    ]
