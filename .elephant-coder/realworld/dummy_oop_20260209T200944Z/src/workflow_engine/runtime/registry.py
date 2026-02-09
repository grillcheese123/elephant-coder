"""Runtime processor registry."""

from workflow_engine.processors.email_processor import EmailProcessor
from workflow_engine.processors.push_processor import PushProcessor
from workflow_engine.processors.sms_processor import SmsProcessor
from workflow_engine.processors.webhook_processor import WebhookProcessor
from workflow_engine.runtime.bootstrap import Runtime


def register_processors(runtime: Runtime) -> None:
    """Register all built-in processors."""
    runtime.register_processor(EmailProcessor())
    runtime.register_processor(PushProcessor())
    runtime.register_processor(SmsProcessor())
    runtime.register_processor(WebhookProcessor())
