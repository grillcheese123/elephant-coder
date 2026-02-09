# Elephant Coder Config

output.default: text
model.default: qwen/qwen3-coder-next
model.fallbacks: gpt-4o-mini
model.max_retries: 2
model.retry_backoff_sec: 1.0
budgets.max_input_tokens: 12000
budgets.max_output_tokens: 3000
budgets.max_cost_usd: 1.0
plugins.allowed_permissions: read_fs
