from layered_engine.runtime.registry import build_default_runtime
from layered_engine.models.ticket import Ticket


def main():
    runtime = build_default_runtime()

    email_ticket = Ticket(
        ticket_id="TICKET-001",
        target_channel="email",
        data={"to": "user@example.com", "subject": "Test", "body": "Hello"}
    )

    push_ticket = Ticket(
        ticket_id="TICKET-002",
        target_channel="push",
        data={"title": "Alert", "message": "Test push"}
    )

    results = {}

    # Dispatch email ticket
    email_result = runtime.dispatch(email_ticket)
    results["email"] = {
        "success": email_result.success,
        "details": email_result.details,
        "audit": email_result.audit[:100] if hasattr(email_result, "audit") and email_result.audit else "N/A"
    }

    # Attempt push ticket
    try:
        push_result = runtime.dispatch(push_ticket)
        results["push"] = {
            "success": push_result.success,
            "details": push_result.details,
            "audit": push_result.audit[:100] if hasattr(push_result, "audit") and push_result.audit else "N/A"
        }
    except LookupError:
        results["push"] = {
            "success": False,
            "details": "Push processor not available",
            "audit": "N/A"
        }

    # Print per-channel summary
    print("=== Dispatch Summary ===")
    for channel, res in results.items():
        print(f"{channel}: {'OK' if res['success'] else 'FAIL'} - {res['details'][:60]}...")
        print(f"  Audit: {res['audit']}")


if __name__ == "__main__":
    main()