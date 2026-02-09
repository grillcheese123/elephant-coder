"""Runtime registry tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cross_module_engine.processors.base_processor import BaseProcessor
from cross_module_engine.runtime.registry import default_processors


class RegistryTest(unittest.TestCase):
    def test_default_processors_are_base_processor_subclasses(self) -> None:
        processors = default_processors()
        self.assertGreaterEqual(len(processors), 3)
        self.assertTrue(all(isinstance(processor, BaseProcessor) for processor in processors))

    def test_channels_are_distinct(self) -> None:
        channels = [processor.supported_channel for processor in default_processors()]
        self.assertEqual(len(set(channels)), len(channels))


if __name__ == "__main__":
    unittest.main()


