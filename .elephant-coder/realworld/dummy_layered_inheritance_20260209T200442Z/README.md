# Dummy Layered Inheritance Project

This synthetic project is designed for benchmarking code-reasoning workflows.

Core ideas:
- Abstract contracts define work items, processors, repositories, and policy rules.
- Concrete implementations extend a layered hierarchy:
  - `BaseProcessor -> GuardedProcessor -> PrioritizedProcessor -> concrete processors`
- Runtime registry wires implementations into a dispatcher service.

The benchmark tasks should infer and follow these source-code rules.

