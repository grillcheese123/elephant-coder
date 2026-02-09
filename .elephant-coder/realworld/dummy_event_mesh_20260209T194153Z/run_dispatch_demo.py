#!/usr/bin/env python3
"""Demo script to dispatch tickets via default runtime."""

from event_mesh.models.ticket import Ticket
from event_mesh.runtime import build_default_runtime


def main():
    runtime = build_default_runtime()

    # Dispatch one email ticket
    email_ticket = Ticket(
        ticket_id="email-001",
        target_channel="email",
        data={"to": "user@example.com", "subject": "Test"}
    )
    email_result = runtime.dispatch(email_ticket)

    # Attempt one push ticket
    push_ticket = Ticket(
        ticket_id="push-001",
        target_channel="push",
        data={"message": "Hello"}
    )
    try:
        push_result = runtime.dispatch(push_ticket)
    except LookupError:
        push_result = None

    # Per-channel summary
    print(f"email: {'ok' if email_result and email_result.success else 'fail'}")
    print(f"push: {'ok' if push_result and push_result.success else 'unavailable'}")


if __name__ == "__main__":
    main()
