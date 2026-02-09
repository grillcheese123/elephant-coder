"""Tests for PushProcessor."""

import unittest

from workflow_engine.models.ticket import Ticket
from workflow_engine.runtime.bootstrap import build_default_runtime


class TestPushProcessor(unittest.TestCase):
    def test_push_dispatch(self) -> None:
        """Test successful push dispatch via default runtime."""
        runtime = build_default_runtime()
        ticket = Ticket(
            identifier="ticket-1",
            channel="push",
            payload={"title": "Test", "body": "Hello"},
        )
        runtime.repository.save(ticket)
        result = runtime.process(ticket)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.processor, "push")


if __name__ == "__main__":
    unittest.main()
