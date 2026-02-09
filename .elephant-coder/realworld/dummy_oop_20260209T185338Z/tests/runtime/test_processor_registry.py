"""Tests for ProcessorRegistry."""

from event_mesh.models.push_ticket import PushTicket
from event_mesh.runtime.processor_registry import ProcessorRegistry


def test_registry_finds_push_processor() -> None:
    registry = ProcessorRegistry()
    ticket = PushTicket(
        ticket_id="pt-123",
        target_channel="push",
        data={"title": "Alert", "body": "Test"},
        device_token="device-token-abc"
    )
    processor = registry.get_processor(ticket)
    assert processor is not None
    assert processor.name == "push"
