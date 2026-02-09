"""Runtime registry for processors."""

from event_mesh.contracts.processor import Processor
from event_mesh.processors.email_processor import EmailProcessor
from event_mesh.processors.push_processor import PushProcessor
from event_mesh.processors.sms_processor import SmsProcessor


def get_processors() -> list[Processor]:
    """Return list of available processors."""
    return [
        EmailProcessor(),
        PushProcessor(),
        SmsProcessor(),
    ]
