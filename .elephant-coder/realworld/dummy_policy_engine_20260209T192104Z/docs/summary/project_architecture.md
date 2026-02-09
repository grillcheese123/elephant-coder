# Project Architecture

## File Map

```
src/policy_engine/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── processor.py      # Processor (ABC)
│   ├── repository.py     # WorkItemRepository (ABC)
│   └── work_item.py      # WorkItem (ABC)
├── models/
│   ├── __init__.py
│   ├── run_result.py     # RunResult (dataclass)
│   └── ticket.py         # Ticket (concrete WorkItem)
```

## Abstract Contracts

- **WorkItem**: Defines `identifier`, `channel`, and `payload` properties.
- **Processor**: Defines `name`, `supports(item)`, and `process(item)`.
- **WorkItemRepository**: Defines `save`, `get`, `list_by_channel`, and `list_all`.

## Concrete Subclasses

- **Ticket**: Implements `WorkItem` with `ticket_id`, `target_channel`, and `data`.
- **RunResult**: Immutable dataclass capturing `processor`, `item_id`, `success`, and `details`.

## Dispatch Flow

1. Work items (e.g., `Ticket`) are persisted via `WorkItemRepository`.
2. A dispatcher retrieves items (e.g., by channel) and selects a `Processor` via `supports()`.
3. The selected processor executes `process(item)` and returns a `RunResult`.
4. Results are stored or reported for observability.