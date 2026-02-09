# Elephant Coder Config

budgets.max_cost_usd: 1.0
budgets.max_input_tokens: 12000
budgets.max_output_tokens: 3000
cognition.capsule_transport.dim: 768
cognition.capsule_transport.enabled: false
cognition.capsule_transport.fingerprint_bits: 96
cognition.capsule_transport.max_items: 48
cognition.capsule_transport.mode: hybrid
cognition.world_model.capsule_dim: 64
cognition.world_model.dim: 1024
cognition.world_model.enabled: true
cognition.world_model.max_edge_facts: 20000
cognition.world_model.max_symbol_facts: 5000
cognition.world_model.semantic_dims: 28
model.default: qwen/qwen3-coder-next
model.fallbacks: gpt-4o-mini
model.max_retries: 2
model.retry_backoff_sec: 1.0
output.default: text
plugins.allowed_permissions: read_fs
