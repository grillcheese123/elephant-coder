"""Demo script to dispatch email and push tickets."""

from cross_module_engine.runtime.registry import ProcessorRegistry
from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult


class MockWorkItem(WorkItem):
    """Minimal mock for testing."""

    def __init__(self, identifier: str, channel: str, payload: dict[str, str]):
        self._id = identifier
        self._channel = channel
        self._payload = payload

    @property
    def identifier(self) -> str:
        return self._id

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def payload(self) -> dict[str, str]:
        return self._payload


def build_default_runtime() -> ProcessorRegistry:
    """Return a fresh ProcessorRegistry with default processors."""
    return ProcessorRegistry()


def main():
    registry = build_default_runtime()
    results = {}

    # Email ticket
    email_item = MockWorkItem("T-100", "email", {"subject": "Demo", "body": "Hello"})
    email_proc = registry.get_processor(email_item)
    email_result = email_proc.process(email_item)
    results["email"] = email_result

    # Push ticket (may raise LookupError)
    push_item = MockWorkItem("T-101", "push", {"title": "Alert", "body": "Urgent"})
    try:
        push_proc = registry.get_processor(push_item)
        push_result = push_proc.process(push_item)
        results["push"] = push_result
    except LookupError:
        results["push"] = RunResult(
            processor="PushProcessor",
            item_id=push_item.identifier,
            success=False,
            details="LookupError: push delivery not available"
        )

    # Per-channel summary
    for ch in ["email", "push"]:
        r = results[ch]
        print(f"{ch}: {'OK' if r.success else 'FAIL'} | {r.details} | channel={r.processor}")

    # Interface-related detail
    print("Interface detail: DeliveryInterface.emit() returns rendered message string.")


if __name__ == "__main__":
    main()
