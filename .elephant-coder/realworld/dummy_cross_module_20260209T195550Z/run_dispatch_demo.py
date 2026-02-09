from cross_module_engine.runtime.registry import build_default_runtime
from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult


class MockEmailTicket(WorkItem):
    @property
    def identifier(self) -> str:
        return "ticket-001"

    @property
    def channel(self) -> str:
        return "email"

    @property
    def payload(self) -> dict[str, str]:
        return {"subject": "Support Request", "body": "User reported login issue."}


class MockPushTicket(WorkItem):
    @property
    def identifier(self) -> str:
        return "ticket-002"

    @property
    def channel(self) -> str:
        return "push"

    @property
    def payload(self) -> dict[str, str]:
        return {"title": "New Update", "body": "Your ticket has been updated."}


def main():
    runtime = build_default_runtime()
    email_item = MockEmailTicket()
    push_item = MockPushTicket()

    results = {}

    # Dispatch email ticket
    email_result = runtime.process(email_item)
    results["email"] = email_result

    # Attempt push ticket
    try:
        push_result = runtime.process(push_item)
        results["push"] = push_result
    except LookupError:
        results["push"] = RunResult(
            processor="PushProcessor",
            item_id=push_item.identifier,
            success=False,
            details="Push delivery not available"
        )

    # Print per-channel summary
    for channel, result in results.items():
        status = "✓" if result.success else "✗"
        print(f"{channel}: {status} | {result.details}")

    # Interface-related detail
    print(f"DeliveryInterface.channel used: {results['email'].processor} via DeliveryInterface.emit")


if __name__ == "__main__":
    main()
