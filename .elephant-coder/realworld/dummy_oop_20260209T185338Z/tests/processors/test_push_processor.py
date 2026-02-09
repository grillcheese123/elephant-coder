"""Tests for PushProcessor."""

import pytest

from event_mesh.models.push_ticket import PushTicket
from event_mesh.processors.push_processor import PushProcessor


def test_push_processor_name() -> None:
    processor = PushProcessor()
    assert processor.name == "push"


def test_push_processor_supports_push_ticket() -> None:
    processor = PushProcessor()
    ticket = PushTicket(
        ticket_id="pt-123",
        target_channel="push",
        data={"title": "Alert", "body": "Test"},
        device_token="device-token-abc"
    )
    assert processor.supports(ticket) is True


def test_push_processor_does_not_support_other_tickets() -> None:
    processor = PushProcessor()
    ticket = PushTicket(
        ticket_id="pt-123",
        target_channel="push",
        data={"title": "Alert", "body": "Test"},
        device_token="device-token-abc"
    )
    ticket.__class__ = type('FakeTicket', (), {
        'identifier': 'fake',
        'channel': 'fake',
        'payload': {}
    })
    assert processor.supports(ticket) is False


def test_push_processor_process_success() -> None:
    processor = PushProcessor()
    ticket = PushTicket(
        ticket_id="pt-123",
        target_channel="push",
        data={"title": "Alert", "body": "Test"},
        device_token="device-token-abc"
    )
    result = processor.process(ticket)
    assert result.success is True
    assert result.processor == "push"
    assert result.item_id == "pt-123"
    assert "Push dispatched" in result.details
