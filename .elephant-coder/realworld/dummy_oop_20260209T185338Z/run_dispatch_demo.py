from event_mesh.processors.email_processor import EmailProcessor
from event_mesh.processors.push_processor import PushProcessor
from event_mesh.models.ticket import Ticket
from event_mesh.models.push_ticket import PushTicket


def main():
    processors = [EmailProcessor(), PushProcessor()]
    items = [
        Ticket(ticket_id="T-001", target_channel="email", data={"to": "user@example.com", "subject": "Welcome"}),
        PushTicket(ticket_id="P-001", target_channel="push", data={"message": "Hello"}, device_token="device-123"),
    ]

    results = []
    for item in items:
        for proc in processors:
            if proc.supports(item):
                results.append(proc.process(item))
                break

    channel_summary = {}
    for r in results:
        channel = r.item_id.split("-")[0].lower()
        channel_summary.setdefault(channel, {"success": 0, "failed": 0})
        if r.success:
            channel_summary[channel]["success"] += 1
        else:
            channel_summary[channel]["failed"] += 1

    for ch, stats in channel_summary.items():
        print(f"{ch}: success={stats['success']}, failed={stats['failed']}")


if __name__ == "__main__":
    main()
