"""Tests for PushProcessor."""

import unittest

from policy_engine.models.ticket import Ticket
from policy_engine.runtime.registry import build_default_runtime


class TestPushProcessor(unittest.TestCase):
    def test_push_dispatch_success(self) -> None:
        """Test successful push dispatch via build_default_runtime."""
        runtime = build_default_runtime()
        push_processor = next(p for p in runtime if p.name == "push")

        ticket = Ticket(
            ticket_id="ticket-123",
            target_channel="push",
            data={"title": "Alert", "body": "System maintenance scheduled"}
        )

        result = push_processor.process(ticket)

        self.assertTrue(result.success)
        self.assertEqual(result.processor, "push")
        self.assertEqual(result.item_id, "ticket-123")
        self.assertIn("Push notification dispatched", result.details)


if __name__ == "__main__":
    unittest.main()
