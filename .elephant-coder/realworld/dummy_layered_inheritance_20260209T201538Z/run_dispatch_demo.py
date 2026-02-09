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
        data={"title": "Alert", "message": "Test push"}
    )
    
    results = {}
    
    email_proc = runtime.find_processor("email")
    if email_proc:
        result = email_proc.process(email_ticket)
        results["email"] = {
            "success": result.success,
            "details": result.details,
            "audit": email_proc.build_audit_prefix() if hasattr(email_proc, 'build_audit_prefix') else "N/A"
        }
    else:
        results["email"] = {"success": False, "details": "No email processor found", "audit": "N/A"}
    
    try:
        push_proc = runtime.find_processor("push")
        if push_proc:
            result = push_proc.process(push_ticket)
            results["push"] = {
                "success": result.success,
                "details": result.details,
                "audit": push_proc.build_audit_prefix() if hasattr(push_proc, 'build_audit_prefix') else "N/A"
            }
        else:
            raise LookupError("No push processor available")
    except LookupError as e:
        results["push"] = {"success": False, "details": str(e), "audit": "N/A"}
    
    print("=== Dispatch Summary ===")
    for channel, res in results.items():
        status = "OK" if res["success"] else "FAIL"
        print(f"{channel}: {status} | {res['details'][:60]}... | audit: {res['audit']}")


if __name__ == "__main__":
    main()
