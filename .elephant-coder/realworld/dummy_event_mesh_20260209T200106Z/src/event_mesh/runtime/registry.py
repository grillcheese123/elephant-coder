"""Runtime processor registry."""

from event_mesh.contracts.processor import Processor
from event_mesh.contracts.work_item import WorkItem
from event_mesh.processors.email_processor import EmailProcessor
from event_mesh.processors.push_processor import PushProcessor
from event_mesh.processors.sms_processor import SmsProcessor


def build_default_runtime() -> dict[str, Processor]:
    """Build the default runtime with all registered processors."""
    return {
        "email": EmailProcessor(),
        "sms": SmsProcessor(),
        "push": PushProcessor(),
    }


def get_processor_for_item(item: WorkItem, registry: dict[str, Processor]) -> Processor | None:
    """Find the first processor that supports the given work item."""
    for name, processor in registry.items():
        if processor.supports(item):
            return processor
    return None
