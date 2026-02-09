# Dummy Cross Module Project

This synthetic project is designed for benchmarking cross-module reasoning.

Core ideas:
- Abstract contracts define work items, processors, repositories, and delivery interfaces.
- Concrete processors use cross-module inheritance:
  - `BaseProcessor -> ChannelBoundProcessor -> ReliableProcessor -> concrete processors`
- Interface implementations are defined in separate modules and consumed by processors.
- Runtime registry wires implementations into a dispatcher service.

The benchmark tasks should infer and follow these source-code rules.

