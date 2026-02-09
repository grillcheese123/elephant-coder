"""Tests for PushProcessor."""

from policy_engine.models.ticket import Ticket
from policy_engine.processors.push_processor import PushProcessor


def test_push_processor_supports_push_channel():
    processor = PushProcessor()
    item = Ticket(
        ticket_id="t1",
        target_channel="push",
        data={"device_token": "dev123", "title": "Alert"},
    )
    assert processor.supports(item) is True


def test_push_processor_rejects_non_push_channel():
    processor = PushProcessor()
    item = Ticket(
        ticket_id="t2",
        target_channel="email",
        data={"to": "user@example.com", "subject": "Hi"},
    )
    assert processor.supports(item) is False


def test_push_processor_delivers_successfully():
    processor = PushProcessor()
    item = Ticket(
        ticket_id="t3",
        target_channel="push",
        data={"device_token": "dev456", "title": "Update"},
    )
    result = processor.process(item)
    assert result.success is True
    assert "push delivered to dev456 with title Update" in result.details
