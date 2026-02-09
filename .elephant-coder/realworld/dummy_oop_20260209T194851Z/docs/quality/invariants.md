# Architectural Invariants

This document describes the extension contracts and architectural invariants that ensure correctness and maintainability of the workflow engine.

## Extension Contracts

### Registry Contract

The registry is responsible for managing available processors and enabling dynamic dispatch based on work item channels.

**Invariants:**
- The registry must support registration of any `Processor` implementation.
- The registry must return a processor for any registered channel.
- The registry must raise `LookupError` for unregistered channels.

**Interface:**
```python
class Registry(ABC):
    @abstractmethod
    def register(self, processor: Processor) -> None: ...

    @abstractmethod
    def get(self, channel: str) -> Processor: ...
```

### Processor Inheritance Rules

All processors must inherit from `BaseProcessor`, which implements the `Processor` contract.

**Invariants:**
- All concrete processors must override `_deliver()` method.
- Processors must not override `name`, `supports`, or `process` methods directly.
- Processors must be stateless or safely shareable across threads.

**Contract:**
```python
class Processor(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def supports(self, item: WorkItem) -> bool: ...

    @abstractmethod
    def process(self, item: WorkItem) -> RunResult: ...
```

### Repository Contract

The repository abstracts persistence of work items, enabling testability and pluggable storage.

**Invariants:**
- `save()` must persist items without side effects on the input.
- `get()` must return `None` for non-existent identifiers.
- `list_by_channel()` and `list_all()` must return fresh lists.

**Interface:**
```python
class WorkItemRepository(ABC):
    @abstractmethod
    def save(self, item: WorkItem) -> None: ...

    @abstractmethod
    def get(self, identifier: str) -> WorkItem | None: ...

    @abstractmethod
    def list_by_channel(self, channel: str) -> list[WorkItem]: ...

    @abstractmethod
    def list_all(self) -> list[WorkItem]: ...
```

## Implementation Examples

- `BaseProcessor` implements `Processor` and delegates delivery via `_deliver()`.
- `InMemoryRepository` implements `WorkItemRepository` using an in-memory dict.
- `Registry` (runtime) registers all known processors at bootstrap.

## Runtime Behavior

These invariants preserve existing runtime behavior: dispatching tickets to appropriate processors, persisting results, and reporting channel summaries.
