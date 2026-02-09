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
│   ├── base_processor.py # BaseProcessor (Processor)
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

- **WorkItem**: Abstract unit of work with `identifier`, `channel`, `payload`
- **Processor**: Abstract processor with `name`, `supports(item)`, `process(item)`
- **WorkItemRepository**: Persistence boundary with `save`, `get`, `list_by_channel`, `list_all`

## Concrete Subclasses

- **WorkItem**: `Ticket`
- **Processor**: `BaseProcessor` (abstract base for concrete processors), `EmailProcessor`, `SmsProcessor`, `WebhookProcessor`
- **WorkItemRepository**: `InMemoryWorkItemRepository`

## Dispatch Flow

1. `Dispatcher` selects appropriate `Processor` via `supports()`
2. `Processor.process()` executes and returns `RunResult`
3. `InMemoryWorkItemRepository` persists `WorkItem` instances
4. `Reporting` and `Registry` coordinate processing and tracking
5. `Bootstrap` initializes runtime components
