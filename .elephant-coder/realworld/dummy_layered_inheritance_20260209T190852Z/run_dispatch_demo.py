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
        data={"device_token": "token123", "message": "Alert"}
    )

    results = {}

    email_result = runtime.dispatch(email_ticket)
    results["email"] = {
        "success": email_result.success,
        "details": email_result.details,
        "audit": email_result.audit if hasattr(email_result, "audit") else []
    }

    try:
        push_result = runtime.dispatch(push_ticket)
        results["push"] = {
            "success": push_result.success,
            "details": push_result.details,
            "audit": push_result.audit if hasattr(push_result, "audit") else []
        }
    except LookupError:
        results["push"] = {
            "success": False,
            "details": "Push processor not available",
            "audit": []
        }

    for channel, res in results.items():
        status = "✓" if res["success"] else "✗"
        print(f"{channel}: {status} {res['details']}")
        if res["audit"]:
            print(f"  Audit: {res['audit'][0] if res['audit'] else 'N/A'}")


if __name__ == "__main__":
    main()