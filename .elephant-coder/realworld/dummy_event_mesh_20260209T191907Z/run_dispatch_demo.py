from event_mesh.runtime import build_default_runtime


def main():
    runtime = build_default_runtime()
    results = []

    # Dispatch email ticket
    email_ticket = runtime.create_ticket(
        ticket_id="email-001",
        target_channel="email",
        data={"to": "user@example.com", "subject": "Test"}
    )
    email_result = runtime.dispatch(email_ticket)
    results.append(email_result)

    # Attempt push ticket
    push_ticket = runtime.create_ticket(
        ticket_id="push-001",
        target_channel="push",
        data={"message": "Test push"}
    )
    try:
        push_result = runtime.dispatch(push_ticket)
        results.append(push_result)
    except LookupError:
        results.append(runtime.create_result(
            processor="push",
            item_id="push-001",
            success=False,
            details="Push processor unavailable"
        ))

    # Per-channel summary
    for r in results:
        print(f"{r.processor}: {'OK' if r.success else 'FAIL'} - {r.details}")


if __name__ == "__main__":
    main()
