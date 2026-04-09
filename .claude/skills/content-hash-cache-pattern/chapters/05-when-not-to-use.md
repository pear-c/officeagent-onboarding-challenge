# When NOT to Use

> 상위 스킬: [content-hash-cache-pattern](../SKILL.md)

- Data that must always be fresh (real-time feeds)
- Cache entries that would be extremely large (consider streaming instead)
- Results that depend on parameters beyond file content (e.g., different extraction configs)
