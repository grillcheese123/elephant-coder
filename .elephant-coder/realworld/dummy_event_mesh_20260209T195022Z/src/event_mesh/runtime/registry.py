"""Runtime processor registry."""

from event_mesh.contracts.processor import Processor
from event_mesh.contracts.work_item import WorkItem
from event_mesh.processors.email_processor import EmailProcessor
from event_mesh.processors.push_processor import PushProcessor
from event_mesh.processors.sms_processor import SmsProcessor


def register_processors() -> list[Processor]:
    """Return list of registered processors."""
    return [
        EmailProcessor(),
        PushProcessor(),
        SmsProcessor(),
    ]


def get_processor_for_item(item: WorkItem, processors: list[Processor]) -> Processor | None:
    """Find processor that supports the given item."""
    for processor in processors:
        if processor.supports(item):
            return processor
    return None
