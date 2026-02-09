from workflow_engine.processors.email_processor import EmailProcessor
from workflow_engine.processors.push_processor import PushProcessor
from workflow_engine.processors.sms_processor import SmsProcessor
from workflow_engine.processors.webhook_processor import WebhookProcessor


def register_processors(runtime):
    """Register all available processors."""
    runtime.register_processor(EmailProcessor())
    runtime.register_processor(PushProcessor())
    runtime.register_processor(SmsProcessor())
    runtime.register_processor(WebhookProcessor())
