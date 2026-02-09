# Benchmark Fairness

## Risks

- **Data leakage**: Training data may leak into benchmarks, inflating scores.
- **Selection bias**: Benchmarks may overrepresent narrow patterns (e.g., common libraries, idioms).
- **Overfitting to metrics**: Models tuned for specific metrics may underperform on real-world tasks.
- **Evaluation instability**: Small changes in prompt or setup may cause large score variations.

## Mitigations

- **Strict isolation**: Ensure no overlap between training corpus and benchmark sources.
- **Diverse coverage**: Include varied codebases, languages, and task types.
- **Robust metrics**: Use multiple metrics (accuracy, latency, correctness, safety) and report confidence intervals.
- **Open evaluation**: Publish prompts, test cases, and scoring logic for reproducibility.
- **Periodic refresh**: Update benchmarks to counter drift and overfitting.