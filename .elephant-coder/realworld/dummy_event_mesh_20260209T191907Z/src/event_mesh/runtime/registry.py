"""Runtime processor registry."""

from event_mesh.contracts.processor import Processor
from event_mesh.processors.email_processor import EmailProcessor
from event_mesh.processors.push_processor import PushProcessor
from event_mesh.processors.sms_processor import SmsProcessor


def build_default_runtime() -> list[Processor]:
    """Return a list of default processors."""
    return [
        EmailProcessor(),
        PushProcessor(),
        SmsProcessor(),
    ]
