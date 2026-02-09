# Project Architecture

## File-level Map

```
src/workflow_engine/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── processor.py          # Processor (ABC)
│   ├── repository.py         # WorkItemRepository (ABC)
│   └── work_item.py          # WorkItem (ABC)
├── models/
│   ├── __init__.py
│   ├── run_result.py         # RunResult (dataclass)
│   └── ticket.py             # Ticket (WorkItem concrete)
├── processors/
│   ├── __init__.py
│   ├── base_processor.py     # BaseProcessor (Processor)
│   ├── email_processor.py    # EmailProcessor (BaseProcessor)
│   ├── sms_processor.py      # SmsProcessor (BaseProcessor)
│   └── webhook_processor.py  # WebhookProcessor (BaseProcessor)
├── repositories/
│   └── in_memory_repository.py  # InMemoryWorkItemRepository (WorkItemRepository)
├── runtime/
│   ├── bootstrap.py          # build_default_runtime
│   └── registry.py           # default_processors
├── services/
│   ├── dispatcher.py         # DispatcherService
│   └── reporting.py          # summarize_channels
└── utils/
    └── ids.py                # make_ticket_id
```

## Abstract Contracts

- **WorkItem** (`contracts/work_item.py`)
  - `identifier: str`
  - `channel: str`
  - `payload: dict[str, str]`

- **WorkItemRepository** (`contracts/repository.py`)
  - `save(item: WorkItem) -> None`
  - `get(identifier: str) -> WorkItem | None`
  - `list_by_channel(channel: str) -> list[WorkItem]`
  - `list_all() -> list[WorkItem]`

- **Processor** (`contracts/processor.py`)
  - `name: str`
  - `supports(item: WorkItem) -> bool`
  - `process(item: WorkItem) -> RunResult`

## Concrete Subclasses

- **WorkItem**: `Ticket` (`models/ticket.py`) — immutable dataclass with `ticket_id`, `target_channel`, `data`
- **Repository**: `InMemoryWorkItemRepository` (`repositories/in_memory_repository.py`) — in-memory dict-backed store
- **Processor**:
  - `BaseProcessor` (`processors/base_processor.py`) — implements `supports` and `process`, declares `_deliver`
  - `EmailProcessor` (`processors/email_processor.py`) — `supported_channel = "email"`
  - `SmsProcessor` (`processors/sms_processor.py`) — `supported_channel = "sms"`
  - `WebhookProcessor` (`processors/webhook_processor.py`) — `supported_channel = "webhook"`

## Dispatch Flow

1. `build_default_runtime()` (`runtime/bootstrap.py`)
   - instantiates `InMemoryWorkItemRepository`
   - calls `default_processors()` (`runtime/registry.py`) to get `[EmailProcessor, SmsProcessor, WebhookProcessor]`
   - returns `(DispatcherService, WorkItemRepository)`

2. `DispatcherService.dispatch(item: WorkItem)` (`services/dispatcher.py`)
   - iterates registered processors
   - calls `processor.supports(item)` to find the first matching processor
   - invokes `processor.process(item)`
   - returns `RunResult`

3. `BaseProcessor.process(item)`
   - checks `supports(item)`; if false, returns failed `RunResult`
   - otherwise calls `_deliver(item)` (implemented by concrete processors)
   - returns successful `RunResult` with details

4. `RunResult` (`models/run_result.py`) — immutable dataclass: `processor`, `item_id`, `success`, `details`