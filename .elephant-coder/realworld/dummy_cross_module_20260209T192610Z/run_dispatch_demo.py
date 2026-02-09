"""Demo script to dispatch email and push tickets."""

from cross_module_engine.runtime.registry import build_default_runtime


def main():
    runtime = build_default_runtime()
    email_item = runtime.repository.get("ticket-email-001")
    push_item = runtime.repository.get("ticket-push-001")

    results = {}

    # Email dispatch
    if email_item:
        for proc in runtime.processors:
            if proc.supports(email_item):
                res = proc.process(email_item)
                results["email"] = f"{res.processor} -> {res.details}"
                break
        else:
            results["email"] = "No processor found"
    else:
        results["email"] = "No item found"

    # Push dispatch (with LookupError handling)
    try:
        if push_item:
            for proc in runtime.processors:
                if proc.supports(push_item):
                    res = proc.process(push_item)
                    results["push"] = f"{res.processor} -> {res.details}"
                    break
            else:
                results["push"] = "No processor found"
        else:
            results["push"] = "No item found"
    except LookupError:
        results["push"] = "Unavailable (LookupError)"

    # Summary output
    print("Per-channel summary:")
    for ch, msg in results.items():
        print(f"  {ch}: {msg}")
    print("Interface detail: DeliveryInterface.emit() returns rendered channel-prefixed message.")


if __name__ == "__main__":
    main()
