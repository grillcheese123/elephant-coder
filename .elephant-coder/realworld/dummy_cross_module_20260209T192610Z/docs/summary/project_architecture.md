# Project Architecture

## File Map
- `src/cross_module_engine/`: core package
  - `contracts/`: abstract interfaces (`Processor`, `WorkItemRepository`, `WorkItem`)
  - `interfaces/`: delivery interface (`DeliveryInterface`)
  - `channels/`: adapter and template (`DeliveryAdapter`, `MessageTemplate`)
  - `processors/`: logic layers (`ChannelBoundProcessor`, `ReliableProcessor`)
  - `models/`: concrete result types (`RunResult`)

## Abstract Contracts
- `WorkItem`: defines `identifier`, `channel`, `payload` (abstract)
- `Processor`: defines `name`, `supports()`, `process()` (abstract)
- `WorkItemRepository`: defines `save()`, `get()`, `list_by_channel()`, `list_all()` (abstract)

## Cross-Module Interfaces
- `DeliveryInterface`: abstracts `channel` property and `emit(message)` method
- `DeliveryAdapter`: implements `DeliveryInterface`, uses `MessageTemplate` for formatting

## Layered Inheritance Chain
`ReliableProcessor` → `ChannelBoundProcessor` → `BaseProcessor` (implicit)
- `ChannelBoundProcessor` depends on `DeliveryInterface` via `adapter` property
- `ReliableProcessor` implements `process()` using `_deliver()` and `render_message()`

## Dispatch Flow
1. `ReliableProcessor.process()` receives `WorkItem`
2. `render_message()` uses `adapter.emit()` → `MessageTemplate.render()`
3. `_deliver()` invokes `emit()` to format and dispatch
4. Result wrapped in `RunResult` returned

All modules follow strict naming and layered dependency rules.