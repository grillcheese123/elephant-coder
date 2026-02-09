"""Unit tests for PushProcessor."""

import unittest

from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult
from cross_module_engine.processors.push_processor import PushProcessor


class MockWorkItem(WorkItem):
    """Mock implementation of WorkItem for testing."""

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
        self.processor = PushProcessor()

    def test_name(self) -> None:
        """Test that processor name is 'push'."""
        self.assertEqual(self.processor.name, "push")

    def test_supports_push_channel(self) -> None:
        """Test that processor supports push channel."""
        item = MockWorkItem("id1", "push", {"message": "Hello"})
        self.assertTrue(self.processor.supports(item))

    def test_does_not_support_non_push_channel(self) -> None:
        """Test that processor does not support non-push channels."""
        item = MockWorkItem("id1", "email", {"message": "Hello"})
        self.assertFalse(self.processor.supports(item))

    def test_process_success(self) -> None:
        """Test successful processing of push item."""
        item = MockWorkItem("id1", "push", {"message": "Hello"})
        result = self.processor.process(item)
        self.assertIsInstance(result, RunResult)
        self.assertTrue(result.success)
        self.assertEqual(result.processor, "push")
        self.assertEqual(result.item_id, "id1")


if __name__ == "__main__":
    unittest.main()
