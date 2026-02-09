from layered_engine.processors.push_processor import PushProcessor
from layered_engine.processors.prioritized_processor import PrioritizedProcessor


def get_processors():
    return [
        PrioritizedProcessor(),
        PushProcessor(),
    ]
