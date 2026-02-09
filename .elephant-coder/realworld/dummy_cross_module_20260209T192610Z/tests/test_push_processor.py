"""Tests for PushProcessor."""

import unittest

from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult
from cross_module_engine.processors.push_processor import PushProcessor


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
    """Test PushProcessor dispatch."""

    def test_process_success(self):
        """Test successful dispatch of push notification."""
        processor = PushProcessor()
        item = MockWorkItem("test-id", "push", {"title": "Test", "body": "Hello"})
        result = processor.process(item)

        self.assertIsInstance(result, RunResult)
        self.assertTrue(result.success)
        self.assertEqual(result.processor, "push")
        self.assertEqual(result.identifier, "test-id")


if __name__ == "__main__":
    unittest.main()
