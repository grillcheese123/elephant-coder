# Project Architecture

## File Map
- `src/cross_module_engine/`: root package
  - `contracts/`: abstract contracts (`Processor`, `WorkItemRepository`, `WorkItem`)
  - `interfaces/`: `DeliveryInterface` (ABC)
  - `channels/`: `MessageTemplate`, `DeliveryAdapter`
  - `processors/`: `ChannelBoundProcessor`, `ReliableProcessor`
  - `models/`: `RunResult`

## Abstract Contracts
- `WorkItem`: defines `identifier`, `channel`, `payload`
- `Processor`: defines `name`, `supports()`, `process()`
- `WorkItemRepository`: defines `save()`, `get()`, `list_by_channel()`, `list_all()`

## Cross-Module Interfaces
- `DeliveryInterface` (ABC) defines `channel` property and `emit()` method
- `DeliveryAdapter` implements `DeliveryInterface`, uses `MessageTemplate` for formatting

## Layered Inheritance Chain
- `ReliableProcessor` → `ChannelBoundProcessor` → `BaseProcessor`
- `DeliveryAdapter` → `DeliveryInterface`

## Dispatch Flow
1. `ReliableProcessor.process()` calls `render_message()`
2. `render_message()` uses `adapter.emit()`
3. `emit()` delegates to `MessageTemplate.render()`
4. Template prepends channel name to content

