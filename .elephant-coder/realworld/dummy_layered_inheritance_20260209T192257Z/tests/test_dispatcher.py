"""Dispatcher behavior tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from layered_engine.models.ticket import Ticket
from layered_engine.runtime.bootstrap import build_default_runtime


class DispatcherTest(unittest.TestCase):
    def test_dispatch_email_item(self) -> None:
        dispatcher, repository = build_default_runtime()
        item = Ticket(
            ticket_id="email-1",
            target_channel="email",
            data={"to": "ops@example.com", "subject": "status"},
        )
        result = dispatcher.dispatch(item)
        self.assertTrue(result.success)
        self.assertIn("email delivered", result.details)
        self.assertEqual(len(repository.list_by_channel("email")), 1)

    def test_dispatch_unknown_channel_raises(self) -> None:
        dispatcher, _ = build_default_runtime()
        item = Ticket(
            ticket_id="push-1",
            target_channel="push",
            data={"device": "dev-1"},
        )
        with self.assertRaises(LookupError):
            dispatcher.dispatch(item)


if __name__ == "__main__":
    unittest.main()


