# Project Architecture

## File Map
- `src/cross_module_engine/` — Core package
  - `contracts/` — Abstract interfaces: `Processor`, `WorkItemRepository`, `WorkItem`
  - `interfaces/` — `DeliveryInterface` (ABC)
  - `channels/` — `MessageTemplate`, `DeliveryAdapter`
  - `processors/` — `ChannelBoundProcessor`, `ReliableProcessor`
  - `models/` — `RunResult`

## Abstract Contracts
- `WorkItem`: identifier, channel, payload (ABC)
- `Processor`: name, supports(), process() (ABC)
- `WorkItemRepository`: save(), get(), list_by_channel(), list_all() (ABC)

## Cross-Module Interfaces
- `DeliveryInterface` (ABC) defines `channel` (property) and `emit(message)`
- `DeliveryAdapter` implements `DeliveryInterface`, uses `MessageTemplate`
- `MessageTemplate` formats payloads as `{channel}:{content}`

## Layered Inheritance Chain
1. `Processor` (ABC)
2. `ChannelBoundProcessor` (extends `Processor`, uses `DeliveryInterface`)
3. `ReliableProcessor` (extends `ChannelBoundProcessor`, implements `process()`)

## Dispatch Flow
1. `ReliableProcessor.process()` receives `WorkItem`
2. `render_message()` uses `adapter.emit()` → `MessageTemplate.render()`
3. `emit()` returns formatted payload string
4. Delivery handled via `DeliveryInterface` abstraction

All modules follow strict naming and dependency rules, with clear separation of concerns across contracts, interfaces, adapters, and processors.