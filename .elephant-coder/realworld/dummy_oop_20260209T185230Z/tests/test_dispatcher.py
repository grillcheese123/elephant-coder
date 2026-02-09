"""Dispatcher service tests."""

import unittest

from workflow_engine.models.ticket import Ticket
from workflow_engine.repositories.in_memory_repository import InMemoryWorkItemRepository
from workflow_engine.runtime.bootstrap import build_default_runtime
from workflow_engine.services.dispatcher import DispatcherService


class DispatcherTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dispatcher, self.repository = build_default_runtime()

    def test_dispatch_email_item(self) -> None:
        ticket = Ticket(
            ticket_id="ticket-1",
            target_channel="email",
            data={"to": "user@example.com", "subject": "Hello"},
        )
        result = self.dispatcher.dispatch(ticket)
        self.assertTrue(result.success)
        self.assertIn("email delivered", result.details)

    def test_dispatch_push_item(self) -> None:
        ticket = Ticket(
            ticket_id="ticket-2",
            target_channel="push",
            data={"device_token": "token123", "message": "Hello push"},
        )
        result = self.dispatcher.dispatch(ticket)
        self.assertTrue(result.success)
        self.assertIn("push delivered", result.details)

    def test_dispatch_unknown_channel_raises(self) -> None:
        ticket = Ticket(
            ticket_id="ticket-3",
            target_channel="unknown",
            data={},
        )
        result = self.dispatcher.dispatch(ticket)
        self.assertFalse(result.success)
        self.assertIn("unsupported channel", result.details)
