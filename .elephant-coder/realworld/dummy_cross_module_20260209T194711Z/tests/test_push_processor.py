"""Tests for PushProcessor."""

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
    """Unit tests for PushProcessor."""

    def setUp(self) -> None:
        self.processor = PushProcessor()

    def test_name_property(self) -> None:
        self.assertEqual(self.processor.name, "push")

    def test_supports_push_channel(self) -> None:
        item = MockWorkItem("id1", "push", {"message": "Hello"})
        self.assertTrue(self.processor.supports(item))

    def test_does_not_support_non_push_channel(self) -> None:
        item = MockWorkItem("id2", "email", {"message": "Hello"})
        self.assertFalse(self.processor.supports(item))

    def test_process_successfully_dispatches_push(self) -> None:
        item = MockWorkItem("id3", "push", {"message": "Test message"})
        result = self.processor.process(item)

        self.assertIsInstance(result, RunResult)
        self.assertTrue(result.success)
        self.assertEqual(result.identifier, "id3")
        self.assertEqual(result.processor, "push")
        self.assertIn("push:Push notification: Test message", result.output)


if __name__ == "__main__":
    unittest.main()
