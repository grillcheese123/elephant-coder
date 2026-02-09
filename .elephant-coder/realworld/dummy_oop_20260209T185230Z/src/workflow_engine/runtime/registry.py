"""Default processor registry."""

from workflow_engine.contracts.processor import Processor
from workflow_engine.processors.email_processor import EmailProcessor
from workflow_engine.processors.sms_processor import SmsProcessor
from workflow_engine.processors.webhook_processor import WebhookProcessor
from workflow_engine.processors.push_processor import PushProcessor


def default_processors() -> list[Processor]:
    return [
        EmailProcessor(),
        SmsProcessor(),
        WebhookProcessor(),
        PushProcessor(),
    ]
