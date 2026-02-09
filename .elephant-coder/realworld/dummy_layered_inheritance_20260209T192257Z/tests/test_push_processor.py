"""Unit tests for PushProcessor."""

import unittest

from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.processors.push_processor import PushProcessor


class MockPushWorkItem(WorkItem):
    """Mock work item for push channel."""

    def __init__(self, identifier: str, payload: dict[str, str]) -> None:
        self._identifier = identifier
        self._payload = payload
        self._channel = "push"

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
    """Test PushProcessor functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.processor = PushProcessor()

    def test_supports_push_channel(self) -> None:
        """Test that processor supports push channel."""
        item = MockPushWorkItem("id1", {"title": "Test", "message": "Hello", "token": "tok123"})
        self.assertTrue(self.processor.supports(item))

    def test_does_not_support_non_push_channel(self) -> None:
        """Test that processor rejects non-push channels."""
        class MockEmailItem(WorkItem):
            @property
            def identifier(self) -> str:
                return "id1"

            @property
            def channel(self) -> str:
                return "email"

            @property
            def payload(self) -> dict[str, str]:
                return {}

        item = MockEmailItem()
        self.assertFalse(self.processor.supports(item))

    def test_process_success(self) -> None:
        """Test successful push dispatch."""
        item = MockPushWorkItem("id1", {"title": "Alert", "message": "System down", "token": "tok456"})
        result = self.processor.process(item)
        self.assertIsInstance(result, RunResult)
        self.assertTrue(result.success)
        self.assertEqual(result.processor, "push")
        self.assertIn("tok456", result.details)

    def test_process_missing_required_keys(self) -> None:
        """Test that processor rejects items missing required keys."""
        item = MockPushWorkItem("id1", {"title": "Alert"})  # Missing message and token
        result = self.processor.process(item)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
