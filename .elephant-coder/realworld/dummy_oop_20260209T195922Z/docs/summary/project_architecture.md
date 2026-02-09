# Project Architecture

## File Map

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
│   └── ticket.py         # Ticket (WorkItem)
├── processors/
│   ├── base_processor.py # BaseProcessor (Processor)
│   ├── email_processor.py
│   ├── sms_processor.py
│   └── webhook_processor.py
├── repositories/
│   └── in_memory_repository.py
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

- **WorkItem**: Abstract unit of work with `identifier`, `channel`, and `payload` properties.
- **Processor**: Abstract processor with `name`, `supports(item)`, and `process(item)` methods.
- **WorkItemRepository**: Persistence boundary with `save`, `get`, `list_by_channel`, and `list_all` methods.

## Concrete Subclasses

- **WorkItem**: `Ticket` implements identifier, channel, and payload.
- **Processor**: `BaseProcessor` implements core logic; `EmailProcessor`, `SmsProcessor`, `WebhookProcessor` extend it with channel-specific `_deliver` logic.
- **WorkItemRepository**: `InMemoryWorkItemRepository` provides in-memory storage.

## Dispatch Flow

1. `Registry` registers processors (`EmailProcessor`, `SmsProcessor`, `WebhookProcessor`).
2. `Dispatcher` selects a processor via `supports(item)`, then calls `process(item)`.
3. `BaseProcessor.process` invokes `_deliver`, which uses the repository to persist results.
4. `Reporting` and `Bootstrap` integrate with repository and dispatcher for initialization and metrics.