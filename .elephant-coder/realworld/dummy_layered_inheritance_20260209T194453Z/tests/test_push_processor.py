"""Unit tests for PushProcessor."""

import unittest

from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.processors.push_processor import PushProcessor


class MockWorkItem(WorkItem):
    """Mock work item for testing."""

    def __init__(self, identifier: str, channel: str, payload: dict[str, str]):
        self._identifier = identifier
        self._channel = channel
        self._payload = payload

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def payload(self) -> dict[str, str]:
        return self._payload


class TestPushProcessor(unittest.TestCase):
    """Test cases for PushProcessor."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.processor = PushProcessor()

    def test_name(self) -> None:
        """Test that the processor returns the correct name."""
        self.assertEqual(self.processor.name, "push")

    def test_supports_push_channel(self) -> None:
        """Test that the processor supports push channel items."""
        item = MockWorkItem("id1", "push", {"title": "Test", "body": "Hello"})
        self.assertTrue(self.processor.supports(item))

    def test_does_not_support_other_channels(self) -> None:
        """Test that the processor does not support non-push channels."""
        item = MockWorkItem("id2", "email", {"to": "test@example.com", "subject": "Test"})
        self.assertFalse(self.processor.supports(item))

    def test_process_successful_delivery(self) -> None:
        """Test successful push delivery."""
        item = MockWorkItem("id3", "push", {"title": "Test", "body": "Hello"})
        result = self.processor.process(item)

        self.assertIsInstance(result, RunResult)
        self.assertTrue(result.success)
        self.assertEqual(result.processor, "push")
        self.assertEqual(result.item_id, "id3")
        self.assertIn("delivered", result.details.lower())


if __name__ == "__main__":
    unittest.main()
