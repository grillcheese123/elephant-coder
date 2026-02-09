"""Tests for quality_checks module."""

import unittest

from elephant_coder.quality_checks import score_token_reduction


class TestScoreTokenReduction(unittest.TestCase):
    def test_normal_case(self) -> None:
        self.assertAlmostEqual(score_token_reduction(1000, 500), 0.5)
        self.assertAlmostEqual(score_token_reduction(1000, 800), 0.2)
        self.assertAlmostEqual(score_token_reduction(1000, 1000), 0.0)
        self.assertAlmostEqual(score_token_reduction(1000, 0), 1.0)

    def test_zero_baseline(self) -> None:
        self.assertEqual(score_token_reduction(0, 0), 0.0)
        self.assertEqual(score_token_reduction(0, 100), 0.0)


if __name__ == "__main__":
    unittest.main()