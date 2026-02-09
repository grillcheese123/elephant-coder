from layered_engine.runtime.registry import build_default_runtime
from layered_engine.models.ticket import Ticket


def main():
    runtime = build_default_runtime()

    email_ticket = Ticket(
        ticket_id="email-001",
        target_channel="email",
        data={"to": "user@example.com", "subject": "Test", "body": "Hello"}
    )

    push_ticket = Ticket(
        ticket_id="push-001",
        target_channel="push",
        data={"device_id": "dev123", "message": "Alert"}
    )

    results = {}

    # Dispatch email ticket
    email_result = runtime.dispatch(email_ticket)
    results["email"] = email_result

    # Attempt push ticket
    try:
        push_result = runtime.dispatch(push_ticket)
        results["push"] = push_result
    except LookupError:
        results["push"] = None

    # Print per-channel summary
    for channel in ["email", "push"]:
        result = results[channel]
        if result is None:
            print(f"{channel}: skipped (not available)")
        else:
            status = "ok" if result.success else "failed"
            print(f"{channel}: {status} ({result.details})")

    # Audit detail snippets
    print("\nAudit snippets:")
    for channel in ["email", "push"]:
        result = results[channel]
        if result:
            print(f"  {channel}: processor={result.processor}, item_id={result.item_id}")


if __name__ == "__main__":
    main()
