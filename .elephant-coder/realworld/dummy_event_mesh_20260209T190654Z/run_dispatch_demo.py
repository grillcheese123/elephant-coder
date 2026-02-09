from event_mesh.runtime import build_default_runtime


def main():
    runtime = build_default_runtime()

    email_ticket = runtime.create_ticket(
        ticket_id="ticket-001",
        channel="email",
        data={"to": "user@example.com", "subject": "Test"},
    )
    push_ticket = runtime.create_ticket(
        ticket_id="ticket-002",
        channel="push",
        data={},
    )

    results = []

    # Dispatch email ticket
    email_result = runtime.dispatch(email_ticket)
    results.append(email_result)

    # Attempt push ticket
    try:
        push_result = runtime.dispatch(push_ticket)
        results.append(push_result)
    except LookupError:
        results.append(None)  # push not available

    # Per-channel summary
    channel_summary = {}
    for r in results:
        if r is None:
            continue
        ch = r.processor
        channel_summary[ch] = channel_summary.get(ch, {"success": 0, "fail": 0})
        if r.success:
            channel_summary[ch]["success"] += 1
        else:
            channel_summary[ch]["fail"] += 1

    for ch, counts in channel_summary.items():
        print(f"{ch}: success={counts['success']}, fail={counts['fail']}")


if __name__ == "__main__":
    main()
