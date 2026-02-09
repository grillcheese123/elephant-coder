import unittest
from hello_app.main import get_message

class TestSmoke(unittest.TestCase):
    def test_get_message(self):
        self.assertEqual(get_message(), "hello world")

if __name__ == "__main__":
    unittest.main()