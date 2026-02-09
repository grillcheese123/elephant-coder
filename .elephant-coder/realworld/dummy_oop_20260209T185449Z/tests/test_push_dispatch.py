"""Tests for push notification dispatch."""

from policy_engine.models.push_ticket import PushTicket
from policy_engine.processors.push_processor import PushProcessor
from policy_engine.repositories.push_repository import PushRepository
from policy_engine.runtime.dispatcher import Dispatcher


def test_push_dispatch_success() -> None:
    """Test successful push notification dispatch."""
    ticket = PushTicket(
        ticket_id="push-123",
        target_channel="push",
        data={"title": "Alert", "body": "System maintenance"},
    )
    processor = PushProcessor()
    repository = PushRepository()
    dispatcher = Dispatcher(processors=[processor], repository=repository)

    result = dispatcher.dispatch(ticket)

    assert result.success is True
    assert result.processor == "push"
    assert result.item_id == "push-123"
    assert "dispatched successfully" in result.details
    assert repository.get("push-123") is not None
