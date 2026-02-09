from policy_engine.models.ticket import Ticket
from policy_engine.runtime import build_default_runtime


def main():
    runtime = build_default_runtime()

    # Dispatch one email ticket
    email_ticket = Ticket(
        ticket_id="email-001",
        target_channel="email",
        data={"to": "user@example.com", "subject": "Test"}
    )
    email_result = runtime.dispatch(email_ticket)

    # Attempt one push ticket; skip if not available
    push_ticket = Ticket(
        ticket_id="push-001",
        target_channel="push",
        data={"message": "Hello"}
    )
    try:
        push_result = runtime.dispatch(push_ticket)
    except LookupError:
        push_result = None

    # Print per-channel summary
    print(f"email: {'success' if email_result.success else 'failed'} - {email_result.details}")
    print(f"push: {'success' if push_result else 'unavailable'}")


if __name__ == "__main__":
    main()