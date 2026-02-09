"""Unit tests for PushProcessor."""

import unittest

from policy_engine.models.ticket import Ticket
from policy_engine.runtime.registry import build_default_runtime


class TestPushProcessor(unittest.TestCase):
    def test_push_dispatch_success(self) -> None:
        runtime = build_default_runtime()
        processor = next(p for p in runtime if p.name == "push")

        ticket = Ticket(
            ticket_id="ticket-123",
            target_channel="push",
            data={"title": "Alert", "body": "System update"}
        )

        result = processor.process(ticket)

        self.assertTrue(result.success)
        self.assertEqual(result.processor, "push")
        self.assertEqual(result.item_id, "ticket-123")
        self.assertIn("dispatched", result.details)


if __name__ == "__main__":
    unittest.main()
