from event_mesh.runtime import build_default_runtime


def main():
    runtime = build_default_runtime()
    results = []

    # Dispatch one email ticket
    email_ticket = runtime.create_ticket(
        ticket_id="email-001",
        channel="email",
        data={"to": "user@example.com", "subject": "Test"}
    )
    email_result = runtime.dispatch(email_ticket)
    results.append(("email", email_result))

    # Attempt one push ticket, handle missing support
    push_ticket = runtime.create_ticket(
        ticket_id="push-001",
        channel="push",
        data={"message": "Hello"}
    )
    try:
        push_result = runtime.dispatch(push_ticket)
        results.append(("push", push_result))
    except LookupError:
        results.append(("push", None))

    # Print per-channel summary
    for channel, result in results:
        if result is None:
            print(f"{channel}: skipped (not available)")
        else:
            status = "ok" if result.success else "fail"
            print(f"{channel}: {status} - {result.details}")


if __name__ == "__main__":
    main()
