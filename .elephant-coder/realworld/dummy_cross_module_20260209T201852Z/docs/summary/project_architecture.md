# Project Architecture

## File Map
- `src/cross_module_engine/`: main package
  - `contracts/`: abstract contracts
    - `processor.py`: `Processor` (ABC)
    - `repository.py`: `WorkItemRepository` (ABC)
    - `work_item.py`: `WorkItem` (ABC)
  - `interfaces/`: delivery interface
    - `delivery_interface.py`: `DeliveryInterface` (ABC)
  - `channels/`: delivery implementations
    - `message_template.py`: `MessageTemplate`
    - `delivery_adapter.py`: `DeliveryAdapter` (implements `DeliveryInterface`)
  - `processors/`: processing logic
    - `channel_bound_processor.py`: `ChannelBoundProcessor` (extends `BaseProcessor`)
    - `reliable_processor.py`: `ReliableProcessor` (extends `ChannelBoundProcessor`)

## Abstract Contracts
- `WorkItem`: defines `identifier`, `channel`, `payload`
- `Processor`: defines `name`, `supports()`, `process()`
- `WorkItemRepository`: defines `save()`, `get()`, `list_by_channel()`, `list_all()`

## Cross-Module Interfaces
- `DeliveryInterface`: defines `channel` property and `emit()` method
- `DeliveryAdapter`: concrete implementation using `MessageTemplate`

## Layered Inheritance Chain
`ReliableProcessor` → `ChannelBoundProcessor` → `BaseProcessor`
`DeliveryAdapter` → `DeliveryInterface`

## Dispatch Flow
1. `ReliableProcessor.process()` receives `WorkItem`
2. `ChannelBoundProcessor._deliver()` calls `adapter.emit()`
3. `DeliveryAdapter.emit()` uses `MessageTemplate.render()` to format message
4. Result returned as `RunResult`