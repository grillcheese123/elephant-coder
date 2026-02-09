"""Tests for push processor."""

import unittest

from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.ticket import Ticket
from layered_engine.processors.push_processor import PushProcessor


class PushProcessorTest(unittest.TestCase):
    """Unit tests for PushProcessor."""

    def test_push_processor_dispatches_successfully(self) -> None:
        """Test successful push notification dispatch."""
        processor = PushProcessor()
        ticket = Ticket(
            ticket_id="ticket-123",
            target_channel="push",
            data={"title": "Test", "body": "Hello"},
        )

        result = processor.process(ticket)

        self.assertTrue(result.success)
        self.assertEqual(result.processor, "push")
        self.assertEqual(result.item_id, "ticket-123")
        self.assertIn("Push notification dispatched", result.details)

    def test_push_processor_rejects_non_push_channel(self) -> None:
        """Test that non-push items are rejected."""
        processor = PushProcessor()
        ticket = Ticket(
            ticket_id="ticket-456",
            target_channel="email",
            data={"to": "user@example.com", "subject": "Test"},
        )

        result = processor.process(ticket)

        self.assertFalse(result.success)
        self.assertEqual(result.processor, "push")
        self.assertIn("blocked by policy", result.details)


if __name__ == "__main__":
    unittest.main()
