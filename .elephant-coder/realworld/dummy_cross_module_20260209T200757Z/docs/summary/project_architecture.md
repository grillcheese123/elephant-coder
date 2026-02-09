# Project Architecture

## File Map
- `src/cross_module_engine/`: root package
  - `contracts/`: abstract interfaces (`Processor`, `WorkItem`, `WorkItemRepository`)
  - `interfaces/`: delivery interface (`DeliveryInterface`)
  - `channels/`: adapter and template (`DeliveryAdapter`, `MessageTemplate`)
  - `processors/`: logic layers (`ChannelBoundProcessor`, `ReliableProcessor`)
  - `models/`: concrete result types (`RunResult`)

## Abstract Contracts
- `WorkItem`: defines `identifier`, `channel`, `payload` (abstract)
- `Processor`: defines `name`, `supports()`, `process()` (abstract)
- `WorkItemRepository`: defines `save()`, `get()`, `list_by_channel()`, `list_all()` (abstract)

## Cross-Module Interfaces
- `DeliveryInterface` (ABC) declares `channel` property and `emit()` method
- `DeliveryAdapter` implements `DeliveryInterface`, uses `MessageTemplate` for formatting

## Layered Inheritance Chain
1. `Processor` (abstract base)
2. `ChannelBoundProcessor` (extends `Processor`, holds `DeliveryInterface`)
3. `ReliableProcessor` (extends `ChannelBoundProcessor`, implements `process()`)

## Dispatch Flow
1. `ReliableProcessor.process()` invoked with `WorkItem`
2. `ChannelBoundProcessor.render_message()` formats via `MessageTemplate`
3. `ChannelBoundProcessor._deliver()` calls `DeliveryAdapter.emit()`
4. `DeliveryAdapter.emit()` delegates to `MessageTemplate.render()`
5. Result returned as `RunResult`