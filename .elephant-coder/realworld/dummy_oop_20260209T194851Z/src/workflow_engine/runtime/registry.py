"""Runtime processor registry."""

from workflow_engine.contracts.processor import Processor
from workflow_engine.processors.email_processor import EmailProcessor
from workflow_engine.processors.push_processor import PushProcessor
from workflow_engine.processors.sms_processor import SmsProcessor
from workflow_engine.processors.webhook_processor import WebhookProcessor


def get_processors() -> list[Processor]:
    """Return all available processors."""
    return [
        EmailProcessor(),
        PushProcessor(),
        SmsProcessor(),
        WebhookProcessor(),
    ]
