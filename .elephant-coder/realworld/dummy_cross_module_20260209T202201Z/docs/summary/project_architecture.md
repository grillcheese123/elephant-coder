# Project Architecture

## File Map
- `src/cross_module_engine/`: root package
  - `contracts/`: abstract interfaces (`Processor`, `WorkItemRepository`, `WorkItem`)
  - `interfaces/`: delivery interface (`DeliveryInterface`)
  - `channels/`: adapter and template (`DeliveryAdapter`, `MessageTemplate`)
  - `processors/`: logic layers (`ChannelBoundProcessor`, `ReliableProcessor`)
  - `models/`: concrete result types (`RunResult`)

## Abstract Contracts
- `WorkItem`: identifier, channel, payload (immutable unit of work)
- `Processor`: name, supports(), process() (handles items)
- `WorkItemRepository`: save(), get(), list_by_channel(), list_all() (persistence boundary)

## Cross-Module Interfaces
- `DeliveryInterface`: channel (property), emit(message) -> str (abstract delivery contract)
- `DeliveryAdapter`: implements `DeliveryInterface`, uses `MessageTemplate` to format messages
- `MessageTemplate`: renders `{channel}:{content}`

## Layered Inheritance Chain
1. `Processor` (ABC) → `ChannelBoundProcessor` (abstract base with adapter hook)
2. `ChannelBoundProcessor` → `ReliableProcessor` (concrete process logic)
3. `DeliveryInterface` (ABC) → `DeliveryAdapter` (concrete delivery)

## Dispatch Flow
1. `ReliableProcessor.process(item)` calls `render_message(item)` → `_deliver(item)`
2. `_deliver` uses `adapter.emit(message)` → `MessageTemplate.render()` → formatted output
3. `DeliveryAdapter` bridges `Processor` and `MessageTemplate` via channel-bound configuration