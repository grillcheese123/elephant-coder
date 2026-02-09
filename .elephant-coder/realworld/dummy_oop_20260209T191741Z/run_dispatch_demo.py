from workflow_engine.runtime.bootstrap import build_default_runtime
from workflow_engine.models.ticket import Ticket
from workflow_engine.utils.ids import make_ticket_id
from workflow_engine.services.reporting import summarize_channels

def main():
    dispatcher, repo = build_default_runtime()

    # Dispatch email ticket
    email_ticket = Ticket(
        ticket_id=make_ticket_id("email"),
        target_channel="email",
        data={"to": "user@example.com", "subject": "Welcome"}
    )
    dispatcher.dispatch(email_ticket)

    # Attempt push ticket, handle LookupError if unavailable
    try:
        push_ticket = Ticket(
            ticket_id=make_ticket_id("push"),
            target_channel="push",
            data={"message": "Hello"}
        )
        dispatcher.dispatch(push_ticket)
    except LookupError:
        pass

    # Print per-channel summary
    summary = summarize_channels(repo)
    for channel, count in summary.items():
        print(f"{channel}: {count}")

if __name__ == "__main__":
    main()