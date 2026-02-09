"""Unit tests for PushProcessor."""

import unittest

from event_mesh.models.ticket import Ticket
from event_mesh.runtime.registry import build_default_runtime


class TestPushProcessor(unittest.TestCase):
    def test_push_dispatch_success(self) -> None:
        """Test successful push dispatch via build_default_runtime."""
        runtime = build_default_runtime()
        processor = runtime["push"]

        ticket = Ticket(
            ticket_id="ticket-123",
            target_channel="push",
            data={"title": "Test", "body": "Hello"}
        )

        result = processor.process(ticket)

        self.assertTrue(result.success)
        self.assertEqual(result.processor, "push")
        self.assertEqual(result.item_id, "ticket-123")
        self.assertIn("Push notification dispatched", result.details)


if __name__ == "__main__":
    unittest.main()
