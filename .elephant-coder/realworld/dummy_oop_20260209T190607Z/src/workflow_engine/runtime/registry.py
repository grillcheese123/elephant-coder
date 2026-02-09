"""Runtime processor registry."""

from workflow_engine.contracts.processor import Processor
from workflow_engine.contracts.repository import WorkItemRepository
from workflow_engine.processors.email_processor import EmailProcessor
from workflow_engine.processors.push_processor import PushProcessor
from workflow_engine.processors.sms_processor import SmsProcessor
from workflow_engine.processors.webhook_processor import WebhookProcessor


def register_processors(
    repository: WorkItemRepository,
) -> list[Processor]:
    """Register all built-in processors."""
    return [
        EmailProcessor(repository),
        PushProcessor(repository),
        SmsProcessor(repository),
        WebhookProcessor(repository),
    ]
