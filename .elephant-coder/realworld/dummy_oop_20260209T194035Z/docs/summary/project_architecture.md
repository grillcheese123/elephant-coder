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
│   └── ticket.py         # Ticket (WorkItem concrete)
├── processors/
│   ├── base_processor.py # BaseProcessor (Processor concrete)
│   ├── email_processor.py
│   ├── sms_processor.py
│   └── webhook_processor.py
├── repositories/
│   └── in_memory_repository.py
├── runtime/
│   ├── bootstrap.py
│   └── registry.py
└── services/
    ├── dispatcher.py
    └── reporting.py
```

## Abstract Contracts

- **WorkItem**: `identifier`, `channel`, `payload` — unit of work.
- **Processor**: `name`, `supports(item)`, `process(item)` — handles items for a channel.
- **WorkItemRepository**: `save`, `get`, `list_by_channel`, `list_all` — persistence boundary.

## Concrete Subclasses

- **WorkItem**: `Ticket`
- **Processor**: `BaseProcessor` (abstract base for concrete processors), `EmailProcessor`, `SmsProcessor`, `WebhookProcessor`
- **Repository**: `InMemoryWorkItemRepository`

## Dispatch Flow

1. `bootstrap.py` initializes `InMemoryWorkItemRepository`.
2. `registry.py` registers `EmailProcessor`, `SmsProcessor`, `WebhookProcessor`.
3. `dispatcher.py` selects processor via `supports()`, invokes `process()`, and persists `RunResult` via repository.
4. `BaseProcessor._deliver()` delegates to channel-specific `_deliver()` implementations.
5. `reporting.py` reads from repository for analytics.