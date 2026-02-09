"""Tests for PushProcessor."""

import unittest

from workflow_engine.models.ticket import Ticket
from workflow_engine.runtime.bootstrap import build_default_runtime


class TestPushProcessor(unittest.TestCase):
    """Test push processor integration."""

    def test_push_dispatch(self) -> None:
        """Test successful push dispatch."""
        runtime = build_default_runtime()
        ticket = Ticket(
            identifier="ticket-1",
            channel="push",
            payload={"title": "Test", "body": "Hello"},
        )
        result = runtime.process(ticket)
        self.assertEqual(result.status, "ok")


if __name__ == "__main__":
    unittest.main()
