"""Runtime processor registry."""

from layered_engine.contracts.processor import Processor
from layered_engine.processors.push_processor import PushProcessor


def get_processors() -> list[Processor]:
    """Return a list of available processors."""
    return [
        PushProcessor(),
    ]
