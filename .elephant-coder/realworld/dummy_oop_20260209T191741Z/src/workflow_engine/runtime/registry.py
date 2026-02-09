from workflow_engine.processors import (
    EmailProcessor,
    PushProcessor,
    SmsProcessor,
    WebhookProcessor,
)
from workflow_engine.runtime.bootstrap import Runtime


def build_default_runtime() -> Runtime:
    """Build a runtime with default processors."""
    runtime = Runtime()
    runtime.register_processor(EmailProcessor())
    runtime.register_processor(PushProcessor())
    runtime.register_processor(SmsProcessor())
    runtime.register_processor(WebhookProcessor())
    return runtime
