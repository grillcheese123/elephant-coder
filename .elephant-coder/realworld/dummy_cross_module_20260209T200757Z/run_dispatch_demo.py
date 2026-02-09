from cross_module_engine.runtime.registry import build_default_runtime
from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult


class MockWorkItem(WorkItem):
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


def main():
    runtime = build_default_runtime()
    email_item = MockWorkItem("T-001", "email", {"subject": "Alert", "body": "System down"})
    push_item = MockWorkItem("T-002", "push", {"title": "Alert", "body": "System down"})

    results = []

    # Dispatch email ticket
    email_result = runtime.process(email_item)
    results.append(("email", email_result))

    # Attempt push ticket
    try:
        push_result = runtime.process(push_item)
        results.append(("push", push_result))
    except LookupError:
        results.append(("push", None))

    # Print per-channel summary
    for channel, result in results:
        if result is None:
            print(f"{channel}: skipped (LookupError: push not available)")
        else:
            print(f"{channel}: {'ok' if result.success else 'fail'} | {result.details} | interface={result.processor}")


if __name__ == "__main__":
    main()
