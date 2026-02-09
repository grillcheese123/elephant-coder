"""Quality metrics for token reduction."""

from __future__ import annotations


def score_token_reduction(baseline_tokens: int, elephant_tokens: int) -> float:
    """Compute token reduction score.

    Returns:
        0.0 if baseline is 0, otherwise (baseline - elephant) / baseline.
    """
    if baseline_tokens == 0:
        return 0.0
    return (baseline_tokens - elephant_tokens) / baseline_tokens
