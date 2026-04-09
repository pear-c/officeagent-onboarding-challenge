# Anti-Patterns to Avoid

> 상위 스킬: [cost-aware-llm-pipeline](../SKILL.md)

- Using the most expensive model for all requests regardless of complexity
- Retrying on all errors (wastes budget on permanent failures)
- Mutating cost tracking state (makes debugging and auditing difficult)
- Hardcoding model names throughout the codebase (use constants or config)
- Ignoring prompt caching for repetitive system prompts
