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
└── services/
    ├── dispatcher.py
    └── reporting.py
```

## Abstract Contracts

- **WorkItem**: defines `identifier`, `channel`, `payload`
- **Processor**: defines `name`, `supports()`, `process()`
- **WorkItemRepository**: defines `save()`, `get()`, `list_by_channel()`, `list_all()`

## Concrete Subclasses

- **WorkItem**: `Ticket`
- **Processor**: `BaseProcessor`, `EmailProcessor`, `SmsProcessor`, `WebhookProcessor`
- **WorkItemRepository**: `InMemoryWorkItemRepository`

## Dispatch Flow

1. `Dispatcher` selects a `Processor` via `supports()`
2. `Processor.process()` executes and persists result via `Repository.save()`
3. `BaseProcessor._deliver()` handles channel-specific delivery
4. `Registry` registers processors; `Bootstrap` initializes runtime

