# Project Architecture

## File Map
- `src/cross_module_engine/`: root package
  - `channels/`: delivery and templating
    - `delivery_adapter.py`: `DeliveryAdapter` implements `DeliveryInterface`
    - `message_template.py`: `MessageTemplate` formats payloads
  - `interfaces/`: abstract contracts
    - `delivery_interface.py`: `DeliveryInterface` (ABC) with `channel` and `emit`
  - `processors/`: processing logic
    - `channel_bound_processor.py`: `ChannelBoundProcessor` extends `BaseProcessor`
    - `reliable_processor.py`: `ReliableProcessor` extends `ChannelBoundProcessor`
  - `contracts/`: domain abstractions
    - `processor.py`: `Processor` (ABC)
    - `repository.py`: `WorkItemRepository` (ABC)
    - `work_item.py`: `WorkItem` (ABC)
  - `models/`: concrete result types
    - `run_result.py`: `RunResult`

## Abstract Contracts
- `WorkItem`: defines `identifier`, `channel`, `payload`
- `Processor`: defines `name`, `supports`, `process`
- `WorkItemRepository`: defines `save`, `get`, `list_by_channel`, `list_all`
- `DeliveryInterface`: defines `channel`, `emit`

## Cross-Module Interfaces
- `DeliveryInterface` → implemented by `DeliveryAdapter`
- `Processor` → extended by `ChannelBoundProcessor` → `ReliableProcessor`
- `WorkItemRepository` → integration point (not yet implemented)

## Layered Inheritance Chain
1. `DeliveryAdapter(DeliveryInterface)`
2. `ChannelBoundProcessor(BaseProcessor)`
3. `ReliableProcessor(ChannelBoundProcessor)`

## Dispatch Flow
1. `ReliableProcessor.process(item)` → `render_message(item)` → `adapter.emit()` → `MessageTemplate.render()`
2. `adapter.emit()` uses `MessageTemplate` to format payload as `{channel}:{content}`
3. `ChannelBoundProcessor._deliver()` orchestrates delivery via `adapter`