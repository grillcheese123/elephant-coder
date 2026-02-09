"""Tests for PushProcessor."""

import unittest

from workflow_engine.models.ticket import Ticket
from workflow_engine.runtime.bootstrap import build_default_runtime


class TestPushProcessor(unittest.TestCase):
    """Test push notification processing."""

    def test_push_dispatch(self) -> None:
        """Test successful push dispatch."""
        runtime = build_default_runtime()
        ticket = Ticket(
            identifier="ticket-1",
            channel="push",
            payload={"title": "Test", "message": "Hello"},
        )
        runtime.repository.save(ticket)

        result = runtime.dispatch(ticket)

        self.assertEqual(result.status, "ok")
        self.assertIn("push_sent", result.message)


if __name__ == "__main__":
    unittest.main()
