# Project Architecture

## File Map

```
src/policy_engine/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── processor.py      # Abstract Processor interface
│   ├── repository.py     # Abstract WorkItemRepository interface
│   └── work_item.py      # Abstract WorkItem interface
├── models/
│   ├── __init__.py
│   ├── run_result.py     # RunResult dataclass
│   └── ticket.py         # Concrete Ticket implementation
```

## Abstract Contracts

- **WorkItem**: Defines `identifier`, `channel`, and `payload` properties for units of work.
- **Processor**: Defines `name`, `supports()`, and `process()` for channel-specific processing.
- **WorkItemRepository**: Defines `save()`, `get()`, `list_by_channel()`, and `list_all()` for persistence.

## Concrete Subclasses

- **Ticket**: Implements WorkItem with `ticket_id`, `target_channel`, and `data` fields.
- **RunResult**: Immutable dataclass capturing processing outcomes (`processor`, `item_id`, `success`, `details`).

## Dispatch Flow

1. Work items (e.g., Ticket instances) are retrieved from the repository.
2. Each item is routed to a Processor that supports its channel via `supports()`.
3. The selected Processor executes `process()`, returning a RunResult.
4. Results are persisted or logged for auditability.