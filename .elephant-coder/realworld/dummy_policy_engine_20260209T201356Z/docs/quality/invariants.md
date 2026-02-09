# Architectural Invariants

This document describes the extension contracts and architectural invariants that must be preserved when extending the policy engine.

## Extension Contracts

### Registry Contract

The registry is responsible for managing processors and routing work items to appropriate handlers. It must:

- Support registration and lookup of processors by channel
- Return a `LookupError` when no processor supports a given work item
- Preserve deterministic dispatch behavior

### Processor Inheritance Rules

All processors must implement the `Processor` abstract base class:

- `name`: Human-readable identifier for the processor
- `supports(item: WorkItem) -> bool`: Determine if the processor can handle the item
- `process(item: WorkItem) -> RunResult`: Execute processing and return a result

Processors must be stateless or safely shareable across dispatches.

### Repository Contract

The `WorkItemRepository` abstract base class defines persistence boundaries:

- `save(item: WorkItem) -> None`: Persist an item
- `get(identifier: str) -> WorkItem | None`: Retrieve by ID
- `list_by_channel(channel: str) -> list[WorkItem]`: Filter by channel
- `list_all() -> list[WorkItem]`: Retrieve all items

Implementations must preserve data integrity and isolation.

## Architectural Invariants

- **No runtime behavior changes**: All extensions must preserve existing dispatch, processing, and persistence semantics
- **Contract adherence**: All implementations must strictly follow abstract contracts
- **Deterministic dispatch**: Same input must always yield same output
- **Traceability**: Work items must carry stable identifiers for auditing
- **Channel isolation**: Processors must only handle items for their supported channels