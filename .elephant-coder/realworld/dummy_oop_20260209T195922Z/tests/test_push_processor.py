"""Tests for PushProcessor."""

import unittest

from workflow_engine.models.ticket import Ticket
from workflow_engine.runtime.bootstrap import build_default_runtime


class TestPushProcessor(unittest.TestCase):
    def test_push_dispatch(self) -> None:
        """Test successful push dispatch via build_default_runtime."""
        runtime = build_default_runtime()
        processor = runtime.registry.get("push")
        self.assertIsNotNone(processor)

        ticket = Ticket(
            identifier="ticket-1",
            channel="push",
            payload={"title": "Test", "body": "Hello"},
        )

        result = processor.process(ticket)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.message, "push_dispatched")


if __name__ == "__main__":
    unittest.main()
