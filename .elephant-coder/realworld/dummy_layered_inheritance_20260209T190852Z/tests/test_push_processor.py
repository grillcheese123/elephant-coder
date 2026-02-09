import unittest

from layered_engine.contracts.work_item import WorkItem
from layered_engine.models.run_result import RunResult
from layered_engine.processors.push_processor import PushProcessor


class MockWorkItem(WorkItem):
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
    def setUp(self):
        self.processor = PushProcessor()

    def test_process_push_item_success(self):
        item = MockWorkItem("id1", "push", {"title": "Test", "body": "Hello"})
        result = self.processor.process(item)

        self.assertIsInstance(result, RunResult)
        self.assertEqual(result.processor, "push")
        self.assertEqual(result.item_id, "id1")
        self.assertTrue(result.success)
        self.assertEqual(result.details, "Push delivered")

    def test_process_non_push_item(self):
        item = MockWorkItem("id2", "email", {"to": "test@example.com"})
        result = self.processor.process(item)

        self.assertFalse(result.success)
        self.assertEqual(result.details, "Channel not supported")


if __name__ == "__main__":
    unittest.main()
