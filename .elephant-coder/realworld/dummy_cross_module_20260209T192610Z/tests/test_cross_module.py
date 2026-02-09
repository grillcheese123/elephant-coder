"""Cross-module inheritance and interface behavior tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cross_module_engine.interfaces.delivery_interface import DeliveryInterface
from cross_module_engine.models.ticket import Ticket
from cross_module_engine.processors.channel_bound_processor import ChannelBoundProcessor
from cross_module_engine.processors.email_processor import EmailProcessor
from cross_module_engine.processors.reliable_processor import ReliableProcessor


class CrossModuleTest(unittest.TestCase):
    def test_email_processor_uses_cross_module_chain(self) -> None:
        processor = EmailProcessor()
        self.assertIsInstance(processor, ChannelBoundProcessor)
        self.assertIsInstance(processor, ReliableProcessor)
        self.assertIsInstance(processor.adapter, DeliveryInterface)

    def test_email_result_contains_retry_and_channel_prefix(self) -> None:
        processor = EmailProcessor()
        item = Ticket(
            ticket_id="email-2",
            target_channel="email",
            data={"to": "dev@example.com", "subject": "health"},
        )
        result = processor.process(item)
        self.assertTrue(result.success)
        self.assertIn("[retries=", result.details)
        self.assertIn("email:", result.details)


if __name__ == "__main__":
    unittest.main()

