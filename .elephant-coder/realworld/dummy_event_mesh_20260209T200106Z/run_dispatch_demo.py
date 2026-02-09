from event_mesh.runtime import build_default_runtime


def main():
    runtime = build_default_runtime()
    results = []

    # Dispatch one email ticket
    email_ticket = runtime.create_ticket("ticket-001", "email", {"to": "user@example.com", "subject": "Test"})
    result_email = runtime.dispatch(email_ticket)
    results.append(("email", result_email.success, result_email.details))

    # Attempt one push ticket
    push_ticket = runtime.create_ticket("ticket-002", "push", {"message": "Hello"})
    try:
        result_push = runtime.dispatch(push_ticket)
        results.append(("push", result_push.success, result_push.details))
    except LookupError:
        results.append(("push", False, "push not available"))

    # Print per-channel summary
    for channel, success, details in results:
        status = "OK" if success else "FAIL"
        print(f"{channel}: {status} - {details}")


if __name__ == "__main__":
    main()
