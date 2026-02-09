from event_mesh.runtime import build_default_runtime
from event_mesh.models.ticket import Ticket


def main():
    runtime = build_default_runtime()

    email_ticket = Ticket(
        ticket_id="email-001",
        target_channel="email",
        data={"subject": "Test", "body": "Hello"}
    )
    email_result = runtime.dispatch(email_ticket)

    push_ticket = Ticket(
        ticket_id="push-001",
        target_channel="push",
        data={"title": "Alert", "message": "Test push"}
    )
    try:
        push_result = runtime.dispatch(push_ticket)
    except LookupError:
        push_result = None

    channels = {}
    for result in [email_result, push_result]:
        if result is None:
            continue
        ch = result.processor
        if ch not in channels:
            channels[ch] = {"success": 0, "failed": 0}
        if result.success:
            channels[ch]["success"] += 1
        else:
            channels[ch]["failed"] += 1

    for ch, stats in channels.items():
        print(f"{ch}: success={stats['success']}, failed={stats['failed']}")


if __name__ == "__main__":
    main()
