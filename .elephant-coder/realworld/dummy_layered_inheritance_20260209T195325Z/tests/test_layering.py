"""Layered inheritance behavior tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from layered_engine.models.ticket import Ticket
from layered_engine.processors.email_processor import EmailProcessor
from layered_engine.processors.guarded_processor import GuardedProcessor
from layered_engine.processors.prioritized_processor import PrioritizedProcessor


class LayeringTest(unittest.TestCase):
    def test_email_processor_extends_deep_chain(self) -> None:
        processor = EmailProcessor()
        self.assertIsInstance(processor, GuardedProcessor)
        self.assertIsInstance(processor, PrioritizedProcessor)
        self.assertEqual(processor.priority, 10)

    def test_policy_block_is_exposed_in_result(self) -> None:
        processor = EmailProcessor()
        blocked = Ticket(
            ticket_id="email-blocked",
            target_channel="email",
            data={"to": "ops@example.com"},
        )
        result = processor.process(blocked)
        self.assertFalse(result.success)
        self.assertIn("policy blocked", result.details)
        self.assertIn("priority=10", result.details)


if __name__ == "__main__":
    unittest.main()

