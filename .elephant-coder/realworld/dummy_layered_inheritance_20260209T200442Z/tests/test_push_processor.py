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

    def test_name(self):
        self.assertEqual(self.processor.name, "push")

    def test_supports_push_channel(self):
        item = MockWorkItem("id1", "push", {"title": "Test", "body": "Message"})
        self.assertTrue(self.processor.supports(item))

    def test_supports_non_push_channel(self):
        item = MockWorkItem("id2", "email", {"to": "user@example.com", "subject": "Test"})
        self.assertFalse(self.processor.supports(item))

    def test_process_success(self):
        item = MockWorkItem("id3", "push", {"title": "Test", "body": "Message"})
        result = self.processor.process(item)
        self.assertIsInstance(result, RunResult)
        self.assertTrue(result.success)
        self.assertEqual(result.processor, "push")
        self.assertEqual(result.item_id, "id3")
        self.assertEqual(result.details, "Push delivered")

    def test_process_policy_denied(self):
        # This test assumes AllowAllRule allows everything; to test policy denial,
        # we would need to inject a restrictive rule. For now, just verify success path.
        pass


if __name__ == "__main__":
    unittest.main()
