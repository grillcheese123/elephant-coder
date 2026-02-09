from policy_engine.processors import EmailProcessor, PushProcessor
from policy_engine.models.ticket import Ticket
from policy_engine.models.push_ticket import PushTicket


def main():
    processors = [EmailProcessor(), PushProcessor()]
    items = [
        Ticket(ticket_id="email-001", target_channel="email", data={"to": "user@example.com", "subject": "Welcome"}),
        PushTicket(ticket_id="push-001", target_channel="push", data={"title": "Alert", "body": "New message"}),
    ]

    results_by_channel = {}
    for item in items:
        for processor in processors:
            if processor.supports(item):
                result = processor.process(item)
                channel = item.channel
                results_by_channel.setdefault(channel, []).append(result)
                break

    for channel, results in results_by_channel.items():
        success_count = sum(1 for r in results if r.success)
        print(f"{channel}: {success_count}/{len(results)} processed successfully")


if __name__ == "__main__":
    main()