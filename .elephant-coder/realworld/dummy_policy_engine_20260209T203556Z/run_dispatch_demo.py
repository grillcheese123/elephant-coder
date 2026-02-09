from policy_engine.models.ticket import Ticket
from policy_engine.runtime import build_default_runtime


def main():
    runtime = build_default_runtime()

    email_ticket = Ticket(
        ticket_id="email-001",
        target_channel="email",
        data={"to": "user@example.com", "subject": "Test"}
    )
    push_ticket = Ticket(
        ticket_id="push-001",
        target_channel="push",
        data={"message": "Hello"}
    )

    results = []

    # Dispatch email ticket
    email_result = runtime.dispatch(email_ticket)
    results.append(("email", email_result))

    # Attempt push ticket
    try:
        push_result = runtime.dispatch(push_ticket)
        results.append(("push", push_result))
    except LookupError:
        results.append(("push", None))

    # Per-channel summary
    for channel, result in results:
        if result is None:
            print(f"{channel}: skipped (not available)")
        elif result.success:
            print(f"{channel}: success - {result.details}")
        else:
            print(f"{channel}: failed - {result.details}")


if __name__ == "__main__":
    main()
