# Project Architecture

## File-Level Map

```
src/workflow_engine/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── processor.py      # Processor (ABC)
│   ├── repository.py     # WorkItemRepository (ABC)
│   └── work_item.py      # WorkItem (ABC)
├── models/
│   ├── __init__.py
│   ├── run_result.py     # RunResult (concrete)
│   └── ticket.py         # Ticket (WorkItem concrete)
├── processors/
│   ├── base_processor.py     # BaseProcessor (implements Processor)
│   ├── email_processor.py    # EmailProcessor (extends BaseProcessor)
│   ├── sms_processor.py      # SmsProcessor (extends BaseProcessor)
│   └── webhook_processor.py  # WebhookProcessor (extends BaseProcessor)
├── repositories/
│   └── in_memory_repository.py  # InMemoryWorkItemRepository
├── runtime/
│   ├── bootstrap.py
│   └── registry.py
├── services/
│   ├── dispatcher.py
│   └── reporting.py
└── tests/
    └── test_dispatcher.py
```

## Abstract Contracts

### WorkItem
- `identifier: str`
- `channel: str`
- `payload: dict[str, str]`

### Processor
- `name: str`
- `supports(item: WorkItem) -> bool`
- `process(item: WorkItem) -> RunResult`

### WorkItemRepository
- `save(item: WorkItem) -> None`
- `get(identifier: str) -> WorkItem | None`
- `list_by_channel(channel: str) -> list[WorkItem]`
- `list_all() -> list[WorkItem]`

## Concrete Subclasses

### WorkItem
- `Ticket`: concrete implementation with identifier, channel, payload properties.

### Processor
- `BaseProcessor`: implements `name`, `supports`, `process`, and defines `_deliver(item: WorkItem) -> str` as hook.
- `EmailProcessor`: implements `_deliver` for email delivery.
- `SmsProcessor`: implements `_deliver` for SMS delivery.
- `WebhookProcessor`: implements `_deliver` for webhook delivery.

### Repository
- `InMemoryWorkItemRepository`: in-memory store implementing all repository methods.

## Dispatch Flow

1. **Bootstrap & Registry**: `runtime/bootstrap.py` initializes `InMemoryWorkItemRepository`. `runtime/registry.py` registers `EmailProcessor`, `SmsProcessor`, `WebhookProcessor`.

2. **Dispatcher**: `services/dispatcher.py` receives a `WorkItem`, queries the repository for available processors, uses `supports()` to select the appropriate `Processor`, calls `process()`, and persists the `RunResult` via the repository.

3. **Processing**: Each processor delegates to `_deliver()` to perform channel-specific delivery, returning a `RunResult`.

4. **Reporting**: `services/reporting.py` uses the repository to list and analyze work items and results.

All dependencies are injected via contracts, enabling testability and extensibility.
