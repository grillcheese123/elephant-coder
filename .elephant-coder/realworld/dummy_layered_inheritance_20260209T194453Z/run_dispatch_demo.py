from layered_engine.runtime.registry import build_default_runtime
from layered_engine.models.ticket import Ticket
from layered_engine.models.run_result import RunResult


def main():
    runtime = build_default_runtime()
    
    email_ticket = Ticket(
        ticket_id="T-001",
        target_channel="email",
        data={"to": "user@example.com", "subject": "Test", "body": "Hello"}
    )
    
    push_ticket = Ticket(
        ticket_id="T-002",
        target_channel="push",
        data={"title": "Alert", "message": "Test push"}
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
    print("=== Dispatch Summary ===")
    for channel in ["email", "push"]:
        result = results[channel]
        if result is None:
            print(f"{channel}: skipped (not available)")
        elif isinstance(result, RunResult):
            status = "success" if result.success else "failed"
            print(f"{channel}: {status} ({result.details})")
        else:
            print(f"{channel}: unknown result type")
    
    # Audit detail snippets
    print("\n=== Audit Snippets ===")
    for channel in ["email", "push"]:
        result = results[channel]
        if result and hasattr(result, 'processor'):
            print(f"{channel}: processor={result.processor}, item_id={result.item_id}")


if __name__ == "__main__":
    main()
