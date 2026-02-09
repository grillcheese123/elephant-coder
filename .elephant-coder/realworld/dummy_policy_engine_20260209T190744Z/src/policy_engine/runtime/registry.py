"""Runtime processor registry."""

from policy_engine.contracts.processor import Processor
from policy_engine.processors.email_processor import EmailProcessor
from policy_engine.processors.push_processor import PushProcessor
from policy_engine.processors.sms_processor import SmsProcessor


def build_default_runtime() -> list[Processor]:
    """Build the default runtime processor list."""
    return [
        EmailProcessor(),
        PushProcessor(),
        SmsProcessor(),
    ]
