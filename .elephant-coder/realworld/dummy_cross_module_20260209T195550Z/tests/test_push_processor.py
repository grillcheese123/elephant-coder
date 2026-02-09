"""Tests for PushProcessor."""

import unittest

from cross_module_engine.contracts.work_item import WorkItem
from cross_module_engine.models.run_result import RunResult
from cross_module_engine.processors.push_processor import PushProcessor


class MockWorkItem(WorkItem):
    def __init__(self, channel: str = "push", payload: dict | None = None):
        self._channel = channel
        self._payload = payload or {}

    @property
    def identifier(self) -> str:
        return "test-id"

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def payload(self) -> dict[str, str]:
        return self._payload


class TestPushProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = PushProcessor()

    def test_name(self):
        self.assertEqual(self.processor.name, "push")

    def test_supports_push_channel(self):
        item = MockWorkItem(channel="push")
        self.assertTrue(self.processor.supports(item))

    def test_supports_non_push_channel(self):
        item = MockWorkItem(channel="email")
        self.assertFalse(self.processor.supports(item))

    def test_process_dispatches_successfully(self):
        item = MockWorkItem(channel="push", payload={"message": "Hello"})
        result = self.processor.process(item)
        self.assertIsInstance(result, RunResult)
        self.assertTrue(result.success)
        self.assertIn("push:Hello", result.message)


if __name__ == "__main__":
    unittest.main()
