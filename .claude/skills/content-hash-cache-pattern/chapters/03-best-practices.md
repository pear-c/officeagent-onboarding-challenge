# Best Practices

> 상위 스킬: [content-hash-cache-pattern](../SKILL.md)

- **Hash content, not paths** — paths change, content identity doesn't
- **Chunk large files** when hashing — avoid loading entire files into memory
- **Keep processing functions pure** — they should know nothing about caching
- **Log cache hit/miss** with truncated hashes for debugging
- **Handle corruption gracefully** — treat invalid cache entries as misses, never crash
