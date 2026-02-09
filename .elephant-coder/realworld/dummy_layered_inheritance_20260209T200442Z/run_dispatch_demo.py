from layered_engine.runtime.registry import build_default_runtime
from layered_engine.models.run_result import RunResult


def main():
    runtime = build_default_runtime()
    
    # Create sample work items
    email_item = runtime.repository.get("ticket_email_001")
    if email_item is None:
        email_item = type("WorkItem", (), {
            "identifier": "ticket_email_001",
            "channel": "email",
            "payload": {"to": "user@example.com", "subject": "Ticket #001", "body": "Test email ticket"}
        })()
    
    push_item = type("WorkItem", (), {
        "identifier": "ticket_push_001",
        "channel": "push",
        "payload": {"title": "Ticket #001", "message": "Push notification test"}
    })()
    
    results = []
    
    # Dispatch email ticket
    email_result = None
    for proc in runtime.processors:
        if proc.supports(email_item):
            email_result = proc.process(email_item)
            results.append(email_result)
            break
    
    # Attempt push ticket
    push_result = None
    try:
        for proc in runtime.processors:
            if proc.supports(push_item):
                push_result = proc.process(push_item)
                results.append(push_result)
                break
    except LookupError:
        pass  # Push not available, continue
    
    # Print per-channel summary
    print("=== Dispatch Summary ===")
    for channel in ["email", "push"]:
        channel_results = [r for r in results if r.processor.lower().startswith(channel)]
        status = "OK" if channel_results and any(r.success for r in channel_results) else "FAILED"
        print(f"{channel}: {status}")
    
    # Audit detail snippets
    print("\n=== Audit Details ===")
    for r in results:
        print(f"{r.processor} | {r.item_id} | {'✓' if r.success else '✗'} | {r.details[:60]}...")


if __name__ == "__main__":
    main()
