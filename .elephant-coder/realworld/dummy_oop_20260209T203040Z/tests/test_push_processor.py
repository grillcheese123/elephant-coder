import unittest

from workflow_engine.models.ticket import Ticket
from workflow_engine.runtime.bootstrap import build_default_runtime


class TestPushProcessor(unittest.TestCase):
    def test_push_dispatch(self):
        runtime = build_default_runtime()
        ticket = Ticket(
            identifier="test-push-1",
            channel="push",
            payload={"title": "Test", "body": "Hello"},
        )
        result = runtime.dispatch(ticket)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.processor, "push")


if __name__ == "__main__":
    unittest.main()
